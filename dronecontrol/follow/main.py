import time
import traceback
import asyncio
import cv2
import mediapipe as mp

from mediapipe.python.solution_base import SolutionBase
from mavsdk.action import ActionError

from dronecontrol.common import utils
from dronecontrol.common.video_source import CameraSource, SimulatorSource, RealSenseCameraSource
from dronecontrol.common.pilot import System
from dronecontrol.follow import image_processing
from dronecontrol.follow.controller import Controller

mp_pose = mp.solutions.pose

YAW_POINT = 0.5 # Target mid-point of horizontal axis
FWD_POINT = 2.3 # Target 2.3% of the screen area covered by detected person


def main(ip, simulator=None, use_realsense=False, serial=None, log_to_file=False, port=None):
    global pilot, source, log, controller, file_log, last_run_time
    log = utils.make_stdout_logger(__name__)
    file_log = utils.make_file_logger(__name__) if log_to_file else None
    last_run_time = time.time()

    # Connect with sim when no sim IP provided
    if simulator is not None and not simulator and not serial:
        simulator = utils.get_wsl_host_ip()

    source = get_source(simulator, simulator is not None, use_realsense)
    pilot = System(ip, port, serial is not None, serial)
    controller = Controller(YAW_POINT, FWD_POINT)

    try:
        asyncio.run(run())
    except asyncio.CancelledError:
        log.warning("Cancel program run")
    except KeyboardInterrupt:
        log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
        
    controller.plot()
    close_handlers()


async def run():
    try:
        await pilot.connect()
    except asyncio.exceptions.TimeoutError:
        log.error("Connection time-out")
        return

    with mp_pose.Pose() as pose:
        while True:
            p1, p2 = await process_image(pose)
            await offboard_control(p1, p2)

            try:
                await manual_input_control(pose)
            except KeyboardInterrupt:
                break
            

async def process_image(pose):
    global last_run_time
    image = source.get_frame()
    try:
        results = pose.process(image)
    except Exception as e:
        log.error("Image error: " + str(e))
        results.pose_landmarks = None

    p1, p2 = image_processing.detect(results, image)
    utils.write_text_to_image(image, f"FPS: {round(1.0 / (time.time() - last_run_time))}", 0)
    last_run_time = time.time()
    cv2.imshow("Camera", image)

    await utils.log_system_info(file_log, pilot, results.pose_landmarks)
    return p1, p2


async def fly(yaw, fwd):
    await pilot.set_velocity(forward=fwd, yaw=yaw)
    if fwd == 0: return
    await asyncio.sleep(0.25)
    await pilot.set_velocity()
    await asyncio.sleep(0.1)


async def offboard_control(p1, p2):
    if await pilot.is_offboard():
        yaw, fwd = controller.control(p1, p2)
        log.info(f"Yaw: ({yaw}), Fwd: ({fwd})")
        await fly(yaw, fwd)


async def manual_input_control(pose):
    key = cv2.waitKey(source.get_delay())
    key_action = utils.keyboard_control(key)
    if key_action:
        if System.__name__ in key_action.__qualname__:
            try:
                await key_action(pilot)
            except ActionError as e:
                log.error(e)
                await pilot.abort()
        elif SolutionBase.__name__ in key_action.__qualname__:
            key_action(pose, source.get_blank())


def get_source(ip, use_simulator, use_realsense):
    if use_realsense:
        return RealSenseCameraSource()
    elif use_simulator:
        return SimulatorSource(ip)
    else:
        return CameraSource()


def close_handlers():
    pilot.close()
    utils.close_file_logger(file_log)

    source.close()
    cv2.waitKey(1)
