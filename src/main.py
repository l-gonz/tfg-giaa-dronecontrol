import sys
import asyncio

import mav_system
import camera
import hand_tracking
from hand_tracking import Gesture


def map_gesture_to_action(drone, gesture) -> str:
    if gesture == Gesture.FIST:
        drone.run_action(drone.takeoff)
        return "Gesture: Take-off"


def control_loop(drone, gui, hand, last_gesture):
    img = gui.capture()
    if img is None:
        return 0

    gesture = hand.get_gesture(img)
    if drone.is_idle() and gesture != last_gesture:
        action = map_gesture_to_action(drone, gesture)
        gui.annotate(action)

    gui.render()
    if gui.is_exit():
        raise KeyboardInterrupt

    return gesture


async def main():
    drone = mav_system.drone()

    if not await drone.start():
        sys.exit("System connect time-out")

    gui = camera.handler()
    hand = hand_tracking.tracker()
    last_gesture = 0

    while True:
        try:
            last_gesture = control_loop(drone, gui, hand, last_gesture)
        except KeyboardInterrupt:
            print("Request stop")
            break

    await drone.stop()


if __name__ == "__main__":
    asyncio.run(main())
