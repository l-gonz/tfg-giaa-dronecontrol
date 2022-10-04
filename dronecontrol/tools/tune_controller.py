import asyncio
import cv2
import traceback
from mavsdk.offboard import PositionNedYaw
from mavsdk.action import ActionError
from mediapipe.python.solution_base import SolutionBase

from dronecontrol.common import utils
from dronecontrol.follow.follow import Follow
from dronecontrol.common.pilot import System


class TunePIDController:

    START_POS = PositionNedYaw(0, 0, -2.5, 0)
    MEASURE_TIME = 10
    KP = [4, 5, 6, 7, 8, 9, 10] #list(np.linspace(110, 170, 7))
    KI = [0.001, 0.01, 0.05, 0.08, 2, 10] #list(np.linspace(1, 2, 11))
    KD = [0.005, 0.01, 0.02, 0.03, 0.04, 0.05] #list(np.linspace(0.7, 0.3, 10))

    def __init__(self):
        self.log = utils.make_stdout_logger(__name__)
        self.follow = Follow(port=14550, simulator="") 

        self.follow.is_follow_on = True
        self.follow.is_keyboard_control_on = False
        self.first_time = True

        # No need to poll for outside offboard changes (no RC)
        self.follow.pilot.OFFBOARD_POLL_TIME = 60 * 60 * 12

        self.kp_values = [7]
        self.ki_values = [0.01]
        self.kd_values = [0.03]


    async def run(self):
        await self.follow.connect()
        await asyncio.sleep(5)
        await self.follow.pilot.takeoff()
        await asyncio.sleep(2)
        self.follow.subscribe_to_image(self.on_new_image)
        self.start_pos = await self.follow.pilot.get_position_ned_yaw()

        self.follow.controller.set_yaw_gains(115, 0.16, 60)
        self.follow.controller.set_fwd_gains(7, 0.01, 0.03)

        self.data = []
        self.time = []

        try:
            await self.follow.run()
        except Exception as e:
            self.log.error(e)
            traceback.print_exc()


    async def on_new_image(self, p1, p2):
        if self.first_time:
            await self.follow.pilot.start_offboard()
            self.first_time = False
            self.follow.controller.set_fwd_gains(self.kp_values.pop(0), self.ki_values.pop(0), self.kd_values.pop(0))

        time_data = self.follow.controller.get_time_data(True)
        if time_data and time_data[-1] > self.MEASURE_TIME:
            self.data.append(self.follow.controller.get_fwd_data()[1])
            self.time.append(time_data)
            self.follow.is_follow_on = False
            await self.follow.pilot.set_position_ned_yaw(self.start_pos)
            await asyncio.sleep(2)
            self.follow.controller.reset()
            if len(self.kp_values) > 0:
                self.follow.controller.set_fwd_gains(self.kp_values.pop(0), 
                    self.follow.controller.fwd_pid.Ki, self.follow.controller.fwd_pid.Kd)
                self.log.info(f"Left {len(self.kp_values)}/{len(self.KP)}")
            elif len(self.ki_values) > 0:
                self.follow.controller.set_fwd_gains(self.follow.controller.fwd_pid.Kp, 
                    self.ki_values.pop(0), self.follow.controller.fwd_pid.Kd)
                self.log.info(f"Left {len(self.ki_values)}/{len(self.KI)}")
            elif len(self.kd_values) > 0:
                self.follow.controller.set_fwd_gains(self.follow.controller.fwd_pid.Kp, 
                    self.follow.controller.fwd_pid.Ki, self.kd_values.pop(0))
                self.log.info(f"Left {len(self.kd_values)}/{len(self.KP)}")
            else:
                utils.plot(self.time, self.data, title="Fwd values", legend=self.KP)
            self.follow.is_follow_on = True

        key = cv2.waitKey(1)
        if key == ord(' '):
            await self.verify_tuning()
        else:
            await self.keyboard_control(key)


    async def verify_tuning(self):
        self.follow.log_measures()
        time = self.follow.controller.get_time_data()
        yaw_input = self.follow.controller.get_yaw_data()
        fwd_input = self.follow.controller.get_fwd_data()
        utils.plot(time, yaw_input, subplots=[2,1], block=False, title="Yaw input", ylabel=["H. distance", "Velocity"])
        utils.plot(time, fwd_input, subplots=[2,1], block=False, title="Fwd input", ylabel=["Height", "Velocity"])
        self.follow.is_follow_on = False
        await self.follow.pilot.set_position_ned_yaw(self.start_pos)
        self.follow.controller.reset()
        self.log.info(f"Yaw parameters: Kp {self.follow.controller.yaw_pid.Kp}, Ki {self.follow.controller.yaw_pid.Ki}, Kd {self.follow.controller.yaw_pid.Kd}")
        self.log.info(f"Fwd parameters: Kp {self.follow.controller.fwd_pid.Kp}, Ki {self.follow.controller.fwd_pid.Ki}, Kd {self.follow.controller.fwd_pid.Kd}")
        update = input("Which to update? Y/F: ")
        p = float(input("Enter Kp: "))
        i = float(input("Enter Ki: "))
        d = float(input("Enter Kd: "))
        if update.lower() == 'y':
            self.follow.controller.set_yaw_gains(p, i, d)
        elif update.lower() == 'f':
            self.follow.controller.set_fwd_gains(p, i, d)
        input("Center target, enter to continue")
        
        self.follow.is_follow_on = True


    async def keyboard_control(self, key):
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
        else:
            time_data = self.follow.controller.get_time_data()
            if time_data and int(time_data[-1] - time_data[0]) % 5 == 0:
                self.log.warning(f"Elapsed {time_data[-1] - time_data[0]} seconds")


    def close(self):
        self.log.info("All tasks finished")
        self.follow.close()