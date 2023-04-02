import time
import traceback
import asyncio
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.python.solution_base import SolutionBase
from mavsdk.action import ActionError

from dronecontrol.common import utils, input
from dronecontrol.common.video_source import CameraSource, SimulatorSource
from dronecontrol.common.pilot import System
from dronecontrol.follow import image_processing
from dronecontrol.follow.controller import Controller

mp_pose = mp.solutions.pose

YAW_POINT = 0.5 # Target mid-point of horizontal axis
FWD_POINT_SIM = 0.36 # Target detected person height to 36% of screen height, appropriate for SIMULATOR TESTS
FWD_POINT_CAM = 0.5 # 50% of screen height for real flight camera


class Follow():
    def __init__(self, ip="", port=None, serial=None, simulator_ip=None, log=None):
        """
        Follow-person control solution.

        ip: IP to connect to a pilot system through UDP
        port: port to connect to a pilot system through UDP, defaults to 14540
        serial: address to connect to a pilot system through serial
        simulator_ip: IP to connect to a simulator video source.
                      None defaults to a camera source.
                      Empty string connects to a simulator on localhost.
        log: use an already created logger, makes a new one if None is provided 
        """
        self.log = utils.make_stdout_logger(__name__) if log is None else log
        self.input_handler = input.InputHandler()
        self.last_run_time = time.time()
        self.image_events = []
        use_simulator = simulator_ip is not None

        # Connect with sim when no sim IP provided
        if use_simulator and not simulator_ip and not serial:
            simulator = utils.get_wsl_host_ip()
        self.source = self.__get_source(simulator_ip, use_simulator)

        self.pilot = System(ip, port, serial is not None, serial)
        self.controller = Controller(YAW_POINT, FWD_POINT_SIM if use_simulator else FWD_POINT_CAM, not use_simulator)
        self.is_follow_on = True
        self.is_keyboard_control_on = True
        self.measures = {}


    async def run(self):
        """Entry point for the running loop."""
        if not self.pilot.is_ready:
            try:
                await self.pilot.connect()
            except asyncio.exceptions.TimeoutError:
                self.log.error("Connection time-out")
                return

        # Option: model_complexity=0
        with mp_pose.Pose() as pose:
            self.pose = pose
            while True:
                await measure(self.__process_image, pose)
                await measure(self.__offboard_control, self.p1, self.p2)
                await measure(self.__on_new_image)

                if self.is_keyboard_control_on:
                    try:
                        await measure(self.__manual_input_control, pose)
                    except KeyboardInterrupt:
                        break
                
                await measure(asyncio.sleep, 0.001)


    def subscribe_to_image(self, func):
        """Subscribe a function to the image event,
        to be called everytime a new frame is processed with the detected bounding box."""
        self.image_events.append(func)

    
    async def measure(self, func, *args, is_async=True):
        """Call a function and log the execution time to the measures dictionary."""
        func_name = func.__name__
        if func_name not in self.measures:
            self.measures[func_name] = []
        await utils.measure(func, self.measures[func_name], is_async, *args)


    def log_measures(self):
        """Output average execution time for each recorded function across all iterations run."""
        for i, key in enumerate(self.measures):
            if i == 0:
                self.log.info(f"Timing statistics for {len(self.measures[key])} loops")

            if self.measures[key]:
                self.log.info(f"{i} - {key}: mean {np.mean(self.measures[key])} var {np.var(self.measures[key])}")
            self.measures[key] = []


    def close(self):
        """Close external modules and tools."""
        self.pilot.close()
        self.source.close()
        while cv2.waitKey(200) == 0:
            continue

        self.log_measures()
                

    async def __process_image(self, pose):
        """Run pose detection algorithm on a new frame and store bounding box."""
        image = await measure(self.source.get_frame, is_async=False)
        try:
            self.results = await measure(pose.process, image, is_async=False)
        except Exception as e:
            self.log.error("Image error: " + str(e))
            self.results.pose_landmarks = None
            try:
                pose.process(self.source.get_blank())
            except:
                pose = mp_pose.Pose()

        self.p1, self.p2 = await measure(image_processing.detect, self.results, image, is_async=False)
        self.__show_image()


    def __show_image(self):
        """Annotate image and show in a window."""
        inputs = Controller.get_input(self.p1, self.p2)
        utils.write_text_to_image(image, f"Yaw input: {inputs[0]:.3} - fwd input: {inputs[1]:.3}")
        utils.write_text_to_image(image, f"Yaw output: {self.controller.last_yaw_vel:.3} - fwd output: {self.controller.last_fwd_vel:.3}", 2)
        utils.write_text_to_image(image, f"FPS: {1.0 / (time.time() - self.last_run_time):.3}", utils.ImageLocation.TOP_LEFT)
        self.last_run_time = time.time()

        try:
            cv2.imshow("Dronecontrol: follow", image)
        except cv2.error as e:
            self.log.error("Error rendering image:\n" + str(e))


    async def __fly(self, yaw, fwd):
        """Make the vehicle move with a set velocity."""
        await self.pilot.set_velocity(forward=fwd, yaw=yaw)


    async def __offboard_control(self, p1, p2):
        """Check offboard control for driving the vehicle."""
        if await self.pilot.is_offboard() and self.is_follow_on:
            yaw, fwd = self.controller.control(p1, p2)
            await self.__fly(yaw, fwd)


    async def __manual_input_control(self, pose):
        """Handle manual input to the pilot through the keyboard."""
        key = cv2.waitKey(self.source.get_delay())
        key_action = self.input_handler.handle(key)
        if key_action:
            if System.__name__ in key_action.__qualname__:
                try:
                    await key_action(self.pilot)
                except ActionError as e:
                    self.log.error(e)
                    await self.pilot.abort()
            elif SolutionBase.__name__ in key_action.__qualname__:
                key_action(pose, self.source.get_blank())


    def __get_source(self, ip, use_simulator):
        """Select video source from the command-line options."""
        if use_simulator:
            return SimulatorSource(ip)
        else:
            return CameraSource()


    async def __on_new_image(self):
        """Call all subscribed functions to the image event."""
        for event in self.image_events:
            try:
                await event(self.p1, self.p2)
            except Exception as e:
                self.log.error(e)


def main(ip="", simulator=None, serial=None, port=None):
    log = utils.make_stdout_logger(__name__)
    follow = Follow(ip, port, serial, simulator, log)

    try:
        asyncio.run(follow.run())
    except asyncio.CancelledError:
        log.warning("Cancel program run")
    except KeyboardInterrupt:
        log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
        
    follow.close()