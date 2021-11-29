import asyncio
import logging

import pilot
import graphics
import mapper


def on_new_gesture(gesture):
    action, params = mapper.map_gesture_to_action(gesture)
    system.queue_action(action, params)


async def main():
    try:
        task = asyncio.create_task(system.start())
    except Exception as error:
        logging.error("Drone crashed\n" + error)
        return

    gui.subscribe_to_gesture(on_new_gesture)

    logging.info("Starting graphics")
    while True:
        gui.capture()
        if gui.render() >= 0:
            break
        await asyncio.sleep(0.03)

    logging.warning("System stop")
    if not task.done():
        task.cancel()
    await task
    logging.info("All tasks finished")


if __name__ == "__main__":
    system = pilot.System()
    gui = graphics.HandGui()
    
    asyncio.run(main())
