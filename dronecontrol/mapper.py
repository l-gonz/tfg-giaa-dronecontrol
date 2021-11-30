import typing
import asyncio

from dronecontrol import graphics, utils
from .gestures import Gesture
from .pilot import System

def map_gesture_to_action(gesture) -> tuple[typing.Callable, dict]:
    """Map a hand gesture to a drone action.
    
    Returns an action function and a parameter dictionary."""
    
    if gesture == Gesture.NO_HAND:
        return System.return_home, {}
    if gesture == Gesture.STOP:
        return System.land, {}
    if gesture == Gesture.FIST:
        return System.takeoff, {}


def on_new_gesture(system, gesture):
    action, params = map_gesture_to_action(gesture)
    system.queue_action(action, params)


async def gui_loop(gui):
    log.info("Starting graphics")
    while True:
        gui.capture()
        if gui.render() >= 0:
            break
        await asyncio.sleep(0.03)


async def cancel_pending(task):
    if not task.done():
        task.cancel()
    await task
    log.info("All tasks finished")


async def run():
    global log
    log = utils.make_logger(__name__)
    system = System()
    gui = graphics.HandGui()
    
    task = asyncio.create_task(system.start())
    gui.subscribe_to_gesture(lambda g: on_new_gesture(system, g))

    await gui_loop(gui)

    log.warning("System stop")
    await cancel_pending(task)


if __name__ == "__main__":
    asyncio.run(run())
