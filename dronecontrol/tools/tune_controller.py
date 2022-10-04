import asyncio
import cv2
from mavsdk.offboard import PositionNedYaw
from mavsdk.action import ActionError
from mediapipe.python.solution_base import SolutionBase

from dronecontrol.common import utils
from dronecontrol.follow.follow import Follow
from dronecontrol.common.pilot import System


class TunePIDController:

    START_POS = PositionNedYaw(0, 0, -2.5, 0)

    def __init__(self):
        self.log = utils.make_stdout_logger(__name__)
        self.follow = Follow(port=14550, simulator="") 

        self.follow.is_follow_on = True
        self.follow.is_keyboard_control_on = False
        self.first_time = True


    async def run(self):
        await self.follow.connect()
        await asyncio.sleep(5)
        await self.follow.pilot.takeoff()
        await asyncio.sleep(2)
        self.follow.subscribe_to_image(self.on_new_image)
        self.start_pos = await self.follow.pilot.get_position_ned_yaw()

        try:
            await self.follow.run()
        except Exception as e:
            self.log.error(e)


    async def on_new_image(self, p1, p2):
        if self.first_time:
            await self.follow.pilot.start_offboard()
            self.first_time = False

        time = self.follow.controller.get_time_data()
        fwd_input = self.follow.controller.get_fwd_data()
        key = cv2.waitKey(1)
        if key == ord(' '):
            utils.plot(time, fwd_input, block=False, title="Fwd input", ylabel="Height")
            self.follow.is_follow_on = False
            await self.follow.pilot.set_position_ned_yaw(self.start_pos)
            self.follow.controller.reset()
            is_yaw = input("Which to update? Y/F: ") == 'Y'
            p = float(input("Enter Kp: "))
            i = float(input("Enter Ki: "))
            d = float(input("Enter Kd: "))
            if is_yaw:
                self.follow.controller.set_yaw_gains(p, i, d)
            else:
                self.follow.controller.set_fwd_gains(p, i, d)
            input("Center target, enter to continue")
            
            self.follow.is_follow_on = True
        else:
            key_action = utils.keyboard_control(key)
            if key_action:
                if System.__name__ in key_action.__qualname__:
                    try:
                        await key_action(self.follow.pilot)
                    except ActionError as e:
                        self.log.error(e)
                        await self.follow.pilot.abort()     
                elif SolutionBase.__name__ in key_action.__qualname__:
                    key_action(self.follow.pose, self.follow.source.get_blank())


    def close(self):
        self.log.info("All tasks finished")
        self.follow.close()