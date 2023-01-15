import asyncio
from datetime import datetime
from enum import Enum
import time
import json
from mavsdk.offboard import PositionNedYaw

from dronecontrol.common import utils
from dronecontrol.follow.follow import Follow

ROTATION_TARGETS = [-150, -100, -50, 50, 100, 150]
DISTANCE_TARGETS = [200, 400, 800, 1000]

class State(Enum):
    RESET = 0 # Position is resetting
    INIT = 1 # Setting test position
    CONTROL = 2 # Controller engaged
    DATA_RECOVERY = 4 # Controller finished


class ControlTest:

    START_POS = PositionNedYaw(0, 0, -2.4, 2)

    def __init__(self, test_yaw=True, data_file=None):
        self.log = utils.make_stdout_logger(__name__)

        # MAVsdk with SITL only works on port 14550, airsim port can be whatever
        # Maybe is because AirSim already starts mavsdk server in default port?
        self.follow = Follow(port=14550, simulator="") 

        self.data = {}
        self.target_index = 0
        self.current_state = State.RESET
        self.log.info(f"Set state to {self.current_state}")
        self.finished = False
        self.test_yaw = test_yaw
        self.targets = ROTATION_TARGETS if test_yaw else DISTANCE_TARGETS
        self.follow.is_follow_on = False

        if data_file:
             with open(data_file, "r") as outfile:
                self.data = json.load(outfile)
                self.plot_data()
                raise KeyboardInterrupt


    async def run(self):
        await self.follow.pilot.connect()
        await asyncio.sleep(5)
        await self.follow.pilot.takeoff()
        await asyncio.sleep(2)
        await self.follow.pilot.set_position_ned_yaw(self.START_POS)
        self.follow.subscribe_to_image(self.on_new_image)

        try:
            await self.follow.run()
        except Exception as e:
            self.log.error(e)
        finally:
            # Save data in case of plotting errors
            if self.data.keys():
                with open(f"data/test-pid-{datetime.now().strftime('%Y%m%d%H%M%S')}.json", "w") as outfile:
                    json.dump(self.data, outfile)


    async def on_new_image(self, p1, p2):
        if self.finished:
            return
        
        if self.current_state == State.RESET:
            if self.has_person_reached_center(p1, p2, 0.01, 0.1):
                self.log.info("REACHED CENTER")
                await self.init_test()

        if self.current_state == State.INIT:
            if self.has_person_left_center(p1, p2):
                await self.start_control()
        if self.current_state == State.CONTROL:
            if self.has_person_reached_center(p1, p2, 0.02, 0.2, check_vel=True):
                await self.stop_control()
        if self.current_state == State.DATA_RECOVERY:
            await self.save_data()


    async def init_test(self):
        await self.follow.pilot.stop_offboard()
        self.follow.is_follow_on = True
        
        self.current_state = State.INIT
        self.log.info(f"Set state to {self.current_state}")
        self.log.info(f"Move person to target horizontal ({self.targets[self.target_index]})")


    async def start_control(self):
        self.log.info(f"Set state to {self.current_state}")
        self.log.info(f"Start control algorithm")
        self.current_state = State.CONTROL
        self.follow.controller.reset()
        self.start_time = time.time()
        await self.follow.pilot.start_offboard()


    async def stop_control(self):
        self.log.info(f"Center achieved, took {time.time() - self.start_time} seconds")
        self.follow.is_follow_on = False
        self.current_state = State.DATA_RECOVERY
        self.log.info(f"Set state to {self.current_state}")

    
    async def save_data(self):
        self.data[self.targets[self.target_index]] = {
            "yaw": self.follow.controller.get_yaw_data(),
            "fwd": self.follow.controller.get_fwd_data(),
            "time": self.follow.controller.get_time_data(True)
        }
        self.log.info(f"Set position velocity to origin")
        await self.follow.pilot.set_position_ned_yaw(self.START_POS)
        await asyncio.sleep(5)

        self.target_index += 1
        if self.target_index == len(self.targets):
            self.finished = True
            self.plot_data()
            raise KeyboardInterrupt
        else:
            self.current_state = State.RESET
            self.log.info(f"Set state to {self.current_state}")
            self.log.info(f"Wait for person in center")

    
    def plot_data(self):
        time = [self.data[target]["time"] for target in self.data]
        yaw_input = [self.data[target]["yaw"][1] for target in self.data]
        fwd_input = [self.data[target]["fwd"][1] for target in self.data]
        utils.plot(time, yaw_input, block=False, title="Yaw input", ylabel="Horizontal distance", legend=self.targets)
        utils.plot(time, fwd_input, title="Fwd input", ylabel="Height", legend=self.targets)


    def close(self):
        self.log.info("All tasks finished")
        self.follow.close()

    def has_pose(self):
        return self.follow.results.pose_landmarks is not None

    def has_person_reached_center(self, p1, p2, yaw_error, fwd_error, check_vel=False):
        return (self.has_pose() 
            and abs(self.follow.controller.get_yaw_error(p1, p2)) < yaw_error
            and abs(self.follow.controller.get_fwd_error(p1, p2)) < fwd_error
            and (not check_vel or self.is_low_speed()))

    def has_person_left_center(self, p1, p2, yaw_error=0.03, fwd_error=0.3):
        return (self.has_pose()
            and (not self.test_yaw or abs(self.follow.controller.get_yaw_error(p1, p2)) > yaw_error)
            and (self.test_yaw or abs(self.follow.controller.get_fwd_error(p1, p2)) > fwd_error))

    def is_low_speed(self):
        return (abs(self.follow.controller.last_yaw_vel) < 0.5
            and abs(self.follow.controller.last_fwd_vel) < 0.1)
