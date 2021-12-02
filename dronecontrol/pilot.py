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


    def __init__(self, port=14540):
        self.is_offboard = False
        self.actions = [] # type: typing.List[Action]
        self.port = port
        self.mav = mavsdk.System()
        self.log = utils.make_logger(__name__)


    async def start(self):
        """
        Start the running loop.
        
        Queued actions will be awaited one at a time
        until they are finished.
        The loop will sleep if the queue is empty.
        """
        # TODO Start drone and ground control

        try:
            await self.__connect()
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
                    await action.func(self, **action.params)
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
        await self.mav.action.takeoff()
        async for state in self.mav.telemetry.landed_state():
            if state == LandedState.IN_AIR:
                break


    async def land(self):
        await self.mav.action.land()
        await self.__landing_finished()


    async def start_offboard(self):
        # TODO WIP
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
        # TODO WIP
        await self.mav.offboard.set_velocity_body(
            VelocityBodyYawspeed(forward, right, -up, yaw))


    async def __landing_finished(self):
        """Runs until the drone has finished landing."""
        async for state in self.mav.telemetry.landed_state():
            if state == LandedState.ON_GROUND:
                break
        async for armed in self.mav.telemetry.armed():
            if not armed:
                self.log.info("Landing complete")
                break

    
    async def __get_relative_altitude(self):
        """Return relative altitude with the ground."""
        async for pos in self.mav.telemetry.position():
            return pos.relative_altitude_m
