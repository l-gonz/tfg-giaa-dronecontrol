import asyncio
import traceback

from dronecontrol.common import utils, pilot
from dronecontrol.hands import graphics
from .gestures import Gesture


def map_gesture_to_action(pilot, gesture):
    """Map a hand gesture to a drone action."""
    
    if gesture == Gesture.NO_HAND:
        return pilot.queue_action(System.hold, interrupt=True)
    if gesture == Gesture.STOP:
        return pilot.queue_action(System.hold)
    if gesture == Gesture.FIST and pilot.current_action_name != System.toggle_takeoff_land.__name__:
        return pilot.queue_action(System.toggle_takeoff_land, interrupt=True)
    if gesture == Gesture.BACKHAND:
        return pilot.queue_action(System.return_home)
    if gesture == Gesture.POINT_UP:
        return pilot.queue_action(System.start_offboard)
    if gesture == Gesture.POINT_RIGHT:
        return pilot.queue_action(System.set_velocity, right=1.0)
    if gesture == Gesture.POINT_LEFT:
        return pilot.queue_action(System.set_velocity, right=-1.0)
    if gesture == Gesture.THUMB_RIGHT:
        return pilot.queue_action(System.set_velocity, forward=1.0)
    if gesture == Gesture.THUMB_LEFT:
        return pilot.queue_action(System.set_velocity, forward=-1.0)
    

async def run_gui(gui: graphics.HandGui):
    """Run loop for the interface to capture
    the image and render it.
    
    Return whether the loop should continue."""

    try:
        gui.capture()
        key = gui.render()
        key_action = utils.keyboard_control(key)
        if key_action:
            pilot.queue_action(key_action, interrupt=True)  
    except Exception as e:
        log.error(e)
        traceback.print_exc()
        return False

    await asyncio.sleep(0.01)
    return True


async def log_loop():
    try:
        while True:
            log.info("LOG loop")
            await utils.log_system_info(file_log, pilot, gui.get_current_gesture())
            await asyncio.sleep(0.1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        log.warning("End of log loop")


async def cancel_pending(*tasks):
    """Stop previous running tasks."""
    for task in tasks:
        if not task.done():
            task.cancel()
        await task
    log.info("All tasks finished")


async def run():
    """Runs the GUI loop and the drone control thread simultaneously."""
    if not pilot.is_ready:
        try:
            await pilot.connect()
        except asyncio.exceptions.TimeoutError:
            log.error("Connection time-out")
            return

    pilot_task = asyncio.create_task(pilot.start_queue())
    gui.subscribe_to_gesture(lambda g: map_gesture_to_action(pilot, g))

    while True:
        if not await run_gui(gui):
            break
        if pilot_task.done():
            break

    log.warning("System stop")
    await cancel_pending(pilot_task)


def close_handlers():
    gui.close()
    pilot.close()
    utils.close_file_logger(file_log)


def main(ip=None, port=None, serial=None, video_file=None, log_to_file=False):
    global log, file_log, pilot, gui
    log = utils.make_stdout_logger(__name__)
    file_log = utils.make_file_logger(__name__) if log_to_file else None

    pilot = pilot.System(ip=ip, port=port, use_serial=serial is not None, serial_address=serial)
    gui = graphics.HandGui(video_file, log_video=log_to_file and not video_file)

    try:
        asyncio.run(run())
    except asyncio.CancelledError:
        log.warning("Cancel program run")
    except KeyboardInterrupt:
        log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
    finally:
        close_handlers()
    