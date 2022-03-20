import asyncio
import cv2
import numpy as np
import mediapipe as mp

from dronecontrol.common import utils
from dronecontrol.common.video_source import SimulatorSource
from dronecontrol.common.pilot import System

mp_pose = mp.solutions.pose


def get_bounding_box(landmarks, size):
    p1_x = int(min(landmarks, key=lambda landmark: landmark.x).x * size[0])
    p2_x = int(max(landmarks, key=lambda landmark: landmark.x).x * size[0])
    p1_y = int(min(landmarks, key=lambda landmark: landmark.y).y * size[1])
    p2_y = int(max(landmarks, key=lambda landmark: landmark.y).y * size[1])

    diff = np.asarray(((p2_x - p1_x) * 0.1, (p2_y - p1_y) * 0.1))
    return np.asarray((p1_x, p1_y)) - diff, np.asarray((p2_x, p2_y)) + diff


async def control_yaw(p1, p2, size):
    mid_point = p1 + (p2 - p1) / 2
    if mid_point[0] < size[0] * 0.45:
        await pilot.set_velocity(yaw=-2)
    elif mid_point[0] > size[0] * 0.55:
        await pilot.set_velocity(yaw=2)
    else:
        await pilot.set_velocity()


async def run():
    await pilot.connect()
    await pilot.takeoff()
    await asyncio.sleep(3)
    await pilot.start_offboard()

    with mp_pose.Pose() as pose:
        while True:
            image = source.get_frame()
            results = pose.process(image)
            if results.pose_landmarks:
                size = (image.shape[1], image.shape[0])
                p1, p2 = get_bounding_box(results.pose_landmarks.landmark, size)
                points = [tuple(map(int, p)) for p in [p1, p2]]
                cv2.rectangle(image, points[0], points[1], (255,0,0), 2, 1)
                await control_yaw(p1, p2, size)

            cv2.imshow("Camera", image)
            if cv2.waitKey(source.get_delay()) == 'r':
                break

    pilot.stop_offboard()
    pilot.land()
    await asyncio.sleep(3)
    source.close()


def main(ip):
    global pilot, source, log
    log = utils.make_logger(__name__)
    source = SimulatorSource(ip)
    pilot = System(14550)

    try:
        asyncio.run(run())
    except asyncio.CancelledError:
        log.warning("Cancel program run")
