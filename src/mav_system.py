import asyncio
import logging
import traceback
from mavsdk import System


class drone():
    def __init__(self, port=14540) -> None:
        self.port = port
        self.system = System()
        self.tasks = []
        # logging.basicConfig(encoding='utf-8', level=logging.DEBUG)


    # def start(self):
    #     connected = asyncio.run(self.__setup())
    #     print("Finish setup")
    #     if connected:
    #         print("Connect success")
    #         asyncio.create_task(self.__thread())
    #         print("System loop started successfully")
    #     return connected

    
    async def stop(self):
        print("Stopping system loop")
        loop = asyncio.get_event_loop()
        # loop.get_tasks()
        # cancel tasks
        

    def is_idle(self) -> bool:
        self.tasks = [task for task in self.tasks if not task.done()]
        return not self.tasks


    def run_action(self, coroutine):
        print("Started new task")
        task = asyncio.create_task(coroutine())
        self.tasks.append(task)
        

    async def takeoff(self):
        print("Sent takeoff to system")
        await self.system.action.arm()
        await self.system.action.takeoff()


    async def start(self):
        try:
            await asyncio.wait_for(self.system.connect(system_address=f"udp://:{self.port}"), timeout=5)
        except asyncio.TimeoutError:
            return False

        print("Waiting for drone to connect...")
        async for state in self.system.core.connection_state():
            if state.is_connected:
                print("Drone discovered!")
                break

        print("Waiting for drone to have a global position estimate...")
        async for health in self.system.telemetry.health():
            if health.is_global_position_ok:
                print("Global position estimate ok")
                break
        return True
