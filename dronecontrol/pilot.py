import asyncio
import typing

import mavsdk
from mavsdk.action import ActionError
from mavsdk.telemetry import LandedState
from mavsdk.offboard import OffboardError, VelocityBodyYawspeed

from dronecontrol import utils


class Action(typing.NamedTuple):
    func: typing.Callable
    params: dict


class System():
    """
    High-level wrapper for a MavSDK system.
    
    Runs queued actions in a loop after start() is called.
    """
    STOP_VELOCITY = VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0)
    WAIT_TIME = 0.05


    def __init__(self, port=14540, serial=None):
        self.is_offboard = False
        self.actions = [] # type: typing.List[Action]
        self.port = port
        self.serial = serial
        self.mav = mavsdk.System()
        self.log = utils.make_logger(__name__)


    async def start(self):
        """
        Start the running loop.
        
        Queued actions will be awaited one at a time
        until they are finished.
        The loop will sleep if the queue is empty.
        """

        try:
            await self.connect()
        except asyncio.exceptions.CancelledError:
            self.log.warning("Connection cancelled")
            return
        except asyncio.exceptions.TimeoutError:
            self.log.error("Connection time-out")
            return

        try:
            while True:
                if len(self.actions) > 0:
                    action = self.actions.pop(0)
                    self.log.info("Execute action: %s", action.func.__name__)
                    try:
                        await asyncio.wait_for(action.func(self, **action.params), timeout=10)
                    except asyncio.exceptions.TimeoutError:
                        self.log.warning(f"Time out waiting for {action.func.__name__}")
                else:
                    await asyncio.sleep(self.WAIT_TIME)
        except asyncio.exceptions.CancelledError:
            self.log.warning("System stop")


    def queue_action(self, func: typing.Callable, params: dict = {}, interrupt: bool = False):
        """
        Add action to queue.
        
        Will be executed after previous actions are finished.
        """
        if interrupt:
            self.clear_queue()
        if func is None:
            return
        action = Action(func, params)
        self.actions.append(action)
        self.log.info("Queue action: %s", func.__name__)


    def clear_queue(self):
        """Clear all pending actions on the system queue."""
        self.actions.clear()
        self.log.warning("Queue cleared")


    async def connect(self):
        """Connect to mavsdk server."""
        # Triggers TimeoutError if it can't connect
        self.log.info("Waiting for drone to connect...")
        
        if self.serial:
            await asyncio.wait_for(self.mav.connect(system_address=f"serial:///dev/{self.serial}"), timeout=30)
        else:
            await asyncio.wait_for(self.mav.connect(system_address=f"udp://:{self.port}"), timeout=5)

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


    async def return_home(self):
        """Return to home position and land."""
        if self.is_offboard:
            await self.stop_offboard()
        try:
            await self.mav.action.return_to_launch()
        except ActionError as error:
            self.log.error("RETURN: " + str(error))

        await self.__landing_finished()
        

    async def takeoff(self):
        """Takeoff.
        
        Finishes when the system arrives at the minimum takeoff altitude."""
        if await self.__get_landed_state() != LandedState.ON_GROUND:
            self.log.warning("Cannot take-off, not on ground")
            return
            
        try:
            await self.mav.action.arm()
        except ActionError as error:
            # if already armed, ignore
            self.log.error("ARM: " + str(error))

        await self.mav.action.takeoff()
        await self.__wait_for_landed_state(LandedState.IN_AIR)


    async def land(self):
        """Land.
        
        Finishes when the system is in the ground."""
        if self.is_offboard:
            await self.stop_offboard()
        await self.mav.action.land()
        await self.__landing_finished()


    async def start_offboard(self):
        """Start offboard mode where the system's movement can be directly controlled."""
        if await self.__get_landed_state() == LandedState.ON_GROUND:
            self.log.warning("Cannot start offboard mode while drone is on the ground")
            return

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
        """Exit offboard mode and return to hold."""
        await self.mav.offboard.set_velocity_body(self.STOP_VELOCITY)

        try:
            await self.mav.offboard.stop()
        except OffboardError as error:
            self.log.error(f"Stopping offboard mode failed with error code: {error._result.result}")
            return

        self.log.info("System exited offboard mode")
        self.is_offboard = False


    async def set_velocity(self, forward=0.0, right=0.0, up=0.0, yaw=0.0):
        """Set the system's velocity in body coordinates."""
        if not self.is_offboard:
            self.log.warning("Cannot set velocity because system is not in offboard mode")
            return
        await self.mav.offboard.set_velocity_body(
            VelocityBodyYawspeed(forward, right, -up, yaw))


    async def __landing_finished(self):
        """Runs until the drone has finished landing."""
        await self.__wait_for_landed_state(LandedState.ON_GROUND)
        async for armed in self.mav.telemetry.armed():
            if not armed:
                self.log.info("Landing complete")
                break

    
    async def __get_landed_state(self):
        """Return current system landed state"""
        async for state in self.mav.telemetry.landed_state():
            return state
    

    async def __wait_for_landed_state(self, state):
        """Wait until the system's landed state match the expected one."""
        async for current_state in self.mav.telemetry.landed_state():
            if state == current_state:
                break


    @staticmethod
    async def get_async_generated(generator):
        async for item in generator:
            return item



async def test():
    drone = System()
    await drone.connect()
    print(await System.get_async_generated(drone.mav.telemetry.position()))
    print(await drone.mav.param.get_param_int("COM_RCL_EXCEPT"))
    await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test())
