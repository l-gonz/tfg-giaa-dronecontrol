import asyncio
import logging

from mavsdk import System
from mavsdk.telemetry import LandedState


class drone():
    def __init__(self, port=14540) -> None:
        self.port = port
        self.system = System()
        self.tasks = []

        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
        self.log.addHandler(handler)


    async def start(self):
        try:
            await asyncio.wait_for(self.system.connect(system_address=f"udp://:{self.port}"), timeout=5)
        except asyncio.TimeoutError:
            return False

        self.log.info("Waiting for drone to connect...")
        async for state in self.system.core.connection_state():
            if state.is_connected:
                self.log.debug("Drone discovered!")
                break

        self.log.debug("Waiting for drone to have a global position estimate...")
        async for health in self.system.telemetry.health():
            if health.is_global_position_ok:
                self.log.debug("Global position estimate ok")
                break
        self.log.info("System ready")
        return True

    
    async def stop(self):
        #TODO Cancel tasks
        for task in self.tasks:
            await task
        

    def is_idle(self) -> bool:
        self.tasks = [task for task in self.tasks if not task.done()]
        return len(self.tasks) == 0


    def run_action(self, coroutine):
        self.log.info("New action " + coroutine.__name__)
        task = asyncio.create_task(coroutine())
        self.tasks.append(task)
        

    async def takeoff(self):
        async for state in self.system.telemetry.landed_state():
            if state != LandedState.ON_GROUND:
                self.log.warn("Cannot take-off, not on ground")
                return
            break
        await self.system.action.arm()
        await self.system.action.takeoff()


    async def land(self):
        await self.system.action.land()


async def main():
    sys = drone()
    await sys.start()
    sys.run_action(sys.takeoff)
    print("Start task.", "tasks:", len(sys.tasks))
    print("Is idle:", sys.is_idle())
    await asyncio.sleep(2)
    print("Is idle:", sys.is_idle())


if __name__ == "__main__":
    asyncio.run(main())
