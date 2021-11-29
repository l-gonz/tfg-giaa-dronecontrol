import asyncio
import logging
from typing import List, NamedTuple

import mavsdk
from mavsdk import telemetry
from mavsdk.action import ActionError
from mavsdk.telemetry import LandedState
from mavsdk.offboard import OffboardError, VelocityBodyYawspeed
from mavsdk.telemetry_pb2 import Position


class System():
    """
    High-level wrapper for a MavSDK system.
    
    Runs queued actions in a loop after start() is called.
    """
    STOP_VELOCITY = VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0)
    WAIT_TIME = 0.05

    is_offboard = False
    actions = [] # type: List[Action]

    def __init__(self, port=14540):
        self.port = port
        self.mav = mavsdk.System()

        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
        self.log.addHandler(handler)


    def queue_action(self, func: function, params: dict):
        """
        Add action to queue.
        
        Will be executed after previous actions are finished.
        """
        action = Action(func, params)
        self.actions.append(action)


    async def start(self):
        """
        Start the running loop.
        
        Queued actions will be awaited one at a time
        until they are finished.
        The loop will sleep if the queue is empty.
        """
        # TODO Should make sure that sim and ground control are running
        # check_dependencies()

        # TODO Check exception propagates to main thread
        await self.__connect()
        
        while True:
            if len(self.actions) > 0:
                action = self.actions.pop(0)
                logging.info("New action: " + action.func.__name__)
                await action.func(**action.params)
            else:
                await asyncio.sleep(self.WAIT_TIME)


    async def __connect(self):
        """Connect to ground control."""
        # Triggers TimeoutError if it can't connect
        await asyncio.wait_for(self.mav.connect(system_address=f"udp://:{self.port}"), timeout=5)

        self.log.info("Waiting for drone to connect...")
        async for state in self.mav.core.connection_state():
            if state.is_connected:
                self.log.debug("Drone discovered!")
                break

        self.log.debug("Waiting for drone to have a global position estimate...")
        async for health in self.mav.telemetry.health():
            if health.is_global_position_ok:
                self.log.debug("Global position estimate ok")
                break
        self.log.info("System ready")

    ###########################
    # TODO Make wait until action is complete
    ###########################

    async def return_home(self):
        """Return to home position and land."""
        if self.is_offboard:
            await self.mav.offboard.set_velocity_body(self.STOP_VELOCITY)
            await self.mav.offboard.stop()
        await self.mav.action.return_to_launch()
        await self.__landing_finished()
        

    async def takeoff(self):
        """Takeoff."""
        async for state in self.mav.telemetry.landed_state():
            if state != LandedState.ON_GROUND:
                self.log.warning("Cannot take-off, not on ground")
                return
            break
        try:
            await self.mav.action.arm()
        except ActionError as error:
            # if already armed, ignore
            self.log.error("ARM: " + error)
        await self.system.action.takeoff()
        async for state in self.mav.telemetry.landed_state():
            if state == LandedState.TAKING_OFF:
                continue
            break
        self.log.info(await self.__get_relative_altitude())


    async def land(self):
        await self.mav.action.land()
        await self.__landing_finished()


    async def start_offboard(self):
        await self.mav.offboard.set_velocity_body(self.STOP_VELOCITY)

        try:
            await self.mav.offboard.start()
        except OffboardError as error:
            self.log.error(f"Starting offboard mode failed with error code: {error._result.result}")
            await self.return_home()
            return

        self.log.info("System in offboard mode")
        self.is_offboard = True

    
    async def stop_offboard(self):
        pass


    async def set_velocity(self, forward=0.0, right=0.0, up=0.0, yaw=0.0):
        await self.mav.offboard.set_velocity_body(
            VelocityBodyYawspeed(forward, right, -up, yaw))


    async def __landing_finished(self):
        async for state in self.mav.telemetry.landed_state():
            if state == LandedState.ON_GROUND:
                self.log.info("Landing complete")
                break

    
    async def __get_relative_altitude(self):
        async for pos in self.mav.telemetry.position():
            return pos.relative_altitude_m()


class Action(NamedTuple):
    func: function
    params: dict


async def main():
    sys = System()
    await sys.start()
    await asyncio.sleep(0.5)
    sys.run_action(sys.takeoff)
    await asyncio.sleep(6)
    await sys.start_offboard()
    sys.run_action(sys.set_velocity, forward=2)
    await asyncio.sleep(3)
    sys.run_action(sys.set_velocity, forward=-2)
    await asyncio.sleep(3)
    await sys.return_home()


if __name__ == "__main__":
    asyncio.run(main())
