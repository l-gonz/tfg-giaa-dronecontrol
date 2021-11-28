import asyncio
import logging

from mavsdk import System
from mavsdk.telemetry import LandedState
from mavsdk.offboard import OffboardError, VelocityBodyYawspeed


class drone():
    STOP_VELOCITY = VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0)

    def __init__(self, port=14540) -> None:
        self.port = port
        self.system = System()
        self.tasks = []
        self.is_offboard = False

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
        for task in self.tasks:
            if not task.done():
                task.cancel()
            await task
        if not self.is_idle:
            self.log.error("Some tasks didn't finish")
        

    @property
    def is_idle(self) -> bool:
        self.tasks = [task for task in self.tasks if not task.done()]
        return len(self.tasks) == 0


    def run_action(self, coroutine, **params):
        self.log.info("New action " + coroutine.__name__)
        if self.is_idle:
            task = asyncio.create_task(coroutine(**params))
            self.tasks.append(task)
        else:
            self.log.error("Tried to start a new task with others pending")


    async def return_failsafe(self):
        # TODO Trigger failsafe if hand detection is lost
        self.log.warning("RETURN FAILSAFE")
        if self.is_offboard:
            await self.system.offboard.set_velocity_body(self.STOP_VELOCITY)
            await self.system.offboard.stop()
        await self.system.action.return_to_launch()
        

    async def takeoff(self):
        async for state in self.system.telemetry.landed_state():
            if state != LandedState.ON_GROUND:
                self.log.warning("Cannot take-off, not on ground")
                return
            break
        await self.system.action.arm()
        await self.system.action.takeoff()


    async def land(self):
        await self.system.action.land()


    async def start_offboard(self):
        await self.system.offboard.set_velocity_body(self.STOP_VELOCITY)

        try:
            await self.system.offboard.start()
        except OffboardError as error:
            self.log.error(f"Starting offboard mode failed with error code: {error._result.result}")
            await self.return_failsafe()
            return

        self.log.info("System in offboard mode")
        self.is_offboard = True

    async def set_velocity(self, forward=0.0, right=0.0, up=0.0, yaw=0.0):
        await self.system.offboard.set_velocity_body(
            VelocityBodyYawspeed(forward, right, -up, yaw))


async def main():
    sys = drone()
    await sys.start()
    await asyncio.sleep(0.5)
    sys.run_action(sys.takeoff)
    await asyncio.sleep(6)
    await sys.start_offboard()
    sys.run_action(sys.set_velocity, forward=2)
    await asyncio.sleep(3)
    sys.run_action(sys.set_velocity, forward=-2)
    await asyncio.sleep(3)
    await sys.return_failsafe()


if __name__ == "__main__":
    asyncio.run(main())
