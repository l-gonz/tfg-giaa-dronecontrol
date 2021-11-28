import asyncio
import logging

import mav_system
import camera
import hand_tracking
from hand_tracking import Gesture


def map_gesture_to_action(drone, gesture) -> str:
    if gesture == Gesture.NO_HAND:
        drone.run_action(drone.land)
        return "Gesture: Land"
    if gesture == Gesture.HAND:
        drone.run_action(drone.takeoff)
        return "Gesture: Take-off"


async def control_loop(drone, gui, hand):
    last_gesture = 0
    action = ""

    while True:
        img = gui.capture()

        gesture = hand.get_gesture(img)
        if drone.is_idle and gesture != last_gesture:
            action = map_gesture_to_action(drone, gesture)
        hand.draw_hands(gui.img)
        gui.annotate(action, 1)
        gui.render()

        # Check for loop end
        if gui.is_exit():
            break

        # Yield control to started actions
        await asyncio.sleep(0.01)
        last_gesture = gesture


async def main():
    drone = mav_system.drone()

    if not await drone.start():
        logging.error("MAV system connect timeout")
        return

    gui = camera.handler()
    hand = hand_tracking.tracker()
    
    await control_loop(drone, gui, hand)

    logging.warning("System stop")
    await drone.stop()


if __name__ == "__main__":
    asyncio.run(main())
