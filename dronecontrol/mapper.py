import asyncio

from dronecontrol import graphics, utils
from .gestures import Gesture
from .pilot import System

def map_gesture_to_action(system, gesture):
    """Map a hand gesture to a drone action."""
    
    if gesture == Gesture.NO_HAND:
        return system.queue_action(System.return_home, interrupt=True)
    if gesture == Gesture.STOP:
        return system.queue_action(System.land)
    if gesture == Gesture.FIST:
        return system.queue_action(System.takeoff)


async def gui_loop(gui):
    """Running loop for the interface to capture
    the image and render it."""
    log.info("Starting graphics")
    while True:
        gui.capture()
        if gui.render() >= 0:
            break
        await asyncio.sleep(0.03)


async def cancel_pending(task):
    """Stop previous running tasks."""
    if not task.done():
        task.cancel()
    await task
    log.info("All tasks finished")


async def run():
    """Runs the GUI loop and the drone control thread simultaneously."""
    global log
    log = utils.make_logger(__name__)
    system = System()
    gui = graphics.HandGui()
    
    task = asyncio.create_task(system.start())
    gui.subscribe_to_gesture(lambda g: map_gesture_to_action(system, g))

    await gui_loop(gui)

    log.warning("System stop")
    await cancel_pending(task)


if __name__ == "__main__":
    asyncio.run(run())
