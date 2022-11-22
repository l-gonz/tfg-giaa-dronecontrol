import time
import traceback
import asyncio
import cv2
import mediapipe as mp
import numpy as np

from mediapipe.python.solution_base import SolutionBase
from mavsdk.action import ActionError

from dronecontrol.common import utils
from dronecontrol.common.video_source import CameraSource, SimulatorSource, RealSenseCameraSource
from dronecontrol.common.pilot import System
from dronecontrol.follow import image_processing
from dronecontrol.follow.controller import Controller

mp_pose = mp.solutions.pose

YAW_POINT = 0.5 # Target mid-point of horizontal axis
FWD_POINT = 0.36 # Target detected person height to 36% of screen height
# Use 0.5 for real flight


class Follow():
    def __init__(self, ip="", port=None, serial=None, simulator=None, use_realsense=False, log=None, log_to_file=False):
        self.log = utils.make_stdout_logger(__name__) if log is None else log
        self.file_log = utils.make_file_logger(__name__) if log_to_file else None
        self.last_run_time = time.time()
        self.image_events = []

        # Connect with sim when no sim IP provided
        if simulator is not None and not simulator and not serial:
            simulator = utils.get_wsl_host_ip()
        self.source = self.__get_source(simulator, simulator is not None, use_realsense)

        self.pilot = System(ip, port, serial is not None, serial, -1)
        self.controller = Controller(YAW_POINT, FWD_POINT)
        self.is_follow_on = True
        self.is_keyboard_control_on = True
        self.measures = {
            "proc_image": [],
            "off_control": [],
            "image_event": [],
            "input": [],
            "end_sleep": [],
            "sub_image_1": [],
            "sub_image_2": [],
            "sub_image_3": [],
        }


    async def run(self):
        if not self.pilot.is_ready:
            try:
                await self.pilot.connect()
            except asyncio.exceptions.TimeoutError:
                self.log.error("Connection time-out")
                return

        with mp_pose.Pose() as pose:
            self.pose = pose
            while True:
                self.p1, self.p2 = await utils.measure(self.__process_image, self.measures["proc_image"], True, pose)
                await utils.measure(self.__offboard_control, self.measures["off_control"], True, self.p1, self.p2)
                await utils.measure(self.__on_new_image, self.measures["image_event"], True)

                if self.is_keyboard_control_on:
                    try:
                        await utils.measure(self.__manual_input_control, self.measures["input"], True, pose)
                    except KeyboardInterrupt:
                        break
                
                await utils.measure(asyncio.sleep, self.measures["end_sleep"], True, 0.001)


    def subscribe_to_image(self, func):
        self.image_events.append(func)


    def log_measures(self):
        for i, key in enumerate(self.measures):
            if i == 0:
                self.log.info(f"Timing statistics for {len(self.measures[key])} loops")

            if self.measures[key]:
                self.log.info(f"{i} - {key}: mean {np.mean(self.measures[key])} var {np.var(self.measures[key])}")
            self.measures[key] = []

    def close(self):
        self.pilot.close()
        utils.close_file_logger(self.file_log)

        self.source.close()
        while cv2.waitKey(200) == 0:
            continue

        self.log_measures()
                

    async def __process_image(self, pose):
        image = await utils.measure(self.source.get_frame, self.measures['sub_image_1'], False)
        try:
            self.results = await utils.measure(pose.process, self.measures['sub_image_2'], False, image)
        except Exception as e:
            self.log.error("Image error: " + str(e))
            self.results.pose_landmarks = None
            pose.process(self.source.get_blank())

        p1, p2 = await utils.measure(image_processing.detect, self.measures['sub_image_3'], False, self.results, image)
        utils.write_text_to_image(image, f"FPS: {round(1.0 / (time.time() - self.last_run_time))}", 0)
        self.last_run_time = time.time()
        try:
            cv2.imshow("Camera", image)
        except cv2.error as e:
            self.log.error("Error rendering image:\n" + str(e))


        await utils.log_system_info(self.file_log, self.pilot, self.results.pose_landmarks)
        return p1, p2


    async def __fly(self, yaw, fwd):
        await self.pilot.set_velocity(forward=fwd, yaw=yaw)
        if fwd == 0: return


    async def __offboard_control(self, p1, p2):
        if await self.pilot.is_offboard(True) and self.is_follow_on:
            yaw, fwd = self.controller.control(p1, p2)
            self.log.info(f"Yaw: ({yaw}), Fwd: ({fwd})")
            await self.__fly(yaw, fwd)


    async def __manual_input_control(self, pose):
        key = cv2.waitKey(self.source.get_delay())
        key_action = utils.keyboard_control(key)
        if key_action:
            if System.__name__ in key_action.__qualname__:
                try:
                    await key_action(self.pilot)
                except ActionError as e:
                    self.log.error(e)
                    await self.pilot.abort()
            elif SolutionBase.__name__ in key_action.__qualname__:
                key_action(pose, self.source.get_blank())


    def __get_source(self, ip, use_simulator, use_realsense):
        if use_realsense:
            return RealSenseCameraSource()
        elif use_simulator:
            return SimulatorSource(ip)
        else:
            return CameraSource()


    async def __on_new_image(self):
        for event in self.image_events:
            try:
                await event(self.p1, self.p2)
            except Exception as e:
                self.log.error(e)


def main(ip="", simulator=None, use_realsense=False, serial=None, log_to_file=False, port=None):
    log = utils.make_stdout_logger(__name__)
    follow = Follow(ip, port, serial, simulator, use_realsense, log, log_to_file)

    try:
        asyncio.run(follow.run())
    except asyncio.CancelledError:
        log.warning("Cancel program run")
    except KeyboardInterrupt:
        log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
        
    follow.close()