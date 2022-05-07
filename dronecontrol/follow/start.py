import asyncio
import cv2
import numpy as np
import mediapipe as mp

from dronecontrol.common import utils
from dronecontrol.common.video_source import CameraSource, SimulatorSource
from dronecontrol.common.pilot import System
from dronecontrol.follow.controller import Controller

mp_pose = mp.solutions.pose

BASE_SPEED = 2
CAMERA_BOX = np.asarray((0, 0)), np.asarray((1, 1))


def detect(results, image):
    size = (image.shape[1], image.shape[0])
    if results.pose_landmarks:
        p1, p2 = get_bounding_box(results.pose_landmarks.landmark)
        cv2.rectangle(image, (p1 * size).astype(int), (p2 * size).astype(int), (255,0,0), 2, 1)
        return p1, p2
        
    return CAMERA_BOX


def get_bounding_box(landmarks):
    p1_x = min(landmarks, key=lambda landmark: landmark.x).x
    p2_x = max(landmarks, key=lambda landmark: landmark.x).x
    p1_y = min(landmarks, key=lambda landmark: landmark.y).y
    p2_y = max(landmarks, key=lambda landmark: landmark.y).y

    # Increase box size by 10% in each dimension
    diff = np.asarray(((p2_x - p1_x) * 0.1, (p2_y - p1_y) * 0.1))
    return np.asarray((p1_x, p1_y)) - diff, np.asarray((p2_x, p2_y)) + diff


async def fly(yaw, fwd):
    await pilot.set_velocity(forward=fwd, yaw=yaw)
    if fwd == 0: return
    await asyncio.sleep(0.25)
    await pilot.set_velocity()
    await asyncio.sleep(0.1)


async def run():
    await pilot.connect()
    await pilot.takeoff()
    await asyncio.sleep(3)
    await pilot.start_offboard()

    with mp_pose.Pose() as pose:
        while True:
            image = source.get_frame()
            try:
                results = pose.process(image)
            except Exception as e:
                log.error("Image error: " + str(e))
                results.pose_landmark = None

            p1, p2 = detect(results, image)
            cv2.imshow("Camera", image)

            yaw, fwd = controller.control(p1, p2)
            print(f"Yaw: ({yaw}), Fwd: ({fwd})")
            await fly(yaw, fwd)

            key = cv2.waitKey(source.get_delay())
            if key == ord('q'):
                break
            elif key == ord('r'):
                pose.process(CameraSource.get_blank())

    await pilot.stop_offboard()
    await pilot.land()
    await asyncio.sleep(3)

    # Clean up
    source.close()
    cv2.waitKey(1)


def get_source(ip, use_simulator):
    if use_simulator:
        return SimulatorSource(ip)
    else:
        return CameraSource()

def main(ip, use_simulator):
    global pilot, source, log, controller
    log = utils.make_logger(__name__)
    source = get_source(ip, use_simulator)
    port = 14550 if use_simulator else 15540 # TODO Unclear !!
    pilot = System(port)
    controller = Controller(0.5, 2.3)

    try:
        asyncio.run(run())
    except asyncio.CancelledError:
        log.warning("Cancel program run")
    except Exception as e:
        log.error("Fatal error: " + str(e))
    finally:
        controller.plot()
