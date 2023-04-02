from simple_pid import PID
from dronecontrol.common import utils

import numpy as np
import time

class Controller:
    """Wrapper class for the simple_pid library.
    
    Implements two PID controllers for obtaining yaw and forward 
    velocity outputs from a detected bounding box."""

    MAX_FWD_VEL = 0.4
    MAX_YAW_VEL = 5
    MAX_HEIGHT_VARIANCE = 2
    ALLOWED_ERROR = 0.02
    ZEROES = np.asarray([0, 0])
    ONES = np.asarray([1, 1])

    DEFAULT_YAW_TUNINGS = (-50, -0.5, 0)
    DEFAULT_YAW_TUNINGS_INV = (50, 0.5, 0)
    DEFAULT_FWD_TUNINGS = (3, 0, 0)

    def __init__(self, target_x, target_height, invert_yaw=False) -> None:
        self.log = utils.make_stdout_logger(__name__)
        
        self.yaw_pid = PID()
        self.yaw_pid.tunings = self.DEFAULT_YAW_TUNINGS if not invert_yaw else self.DEFAULT_YAW_TUNINGS_INV
        self.yaw_pid.setpoint = target_x
        self.yaw_pid.output_limits = (-self.MAX_YAW_VEL, self.MAX_YAW_VEL)

        self.fwd_pid = PID()
        self.fwd_pid.tunings = self.DEFAULT_FWD_TUNINGS
        self.fwd_pid.setpoint = target_height
        self.fwd_pid.output_limits = (-self.MAX_FWD_VEL, self.MAX_FWD_VEL)
        
        self.reset()

    
    def control(self, p1, p2):
        if np.array_equal(p1, self.ZEROES) and np.array_equal(p2, self.ONES):
            return 0, 0

        yaw_input = self.__get_yaw_point_from_box(p1, p2)
        yaw_vel = self.yaw_pid(yaw_input)

        fwd_input = self.__get_fwd_point_from_box(p1, p2)
        fwd_vel = self.fwd_pid(fwd_input)

        # Save detailed measures for visualizing data
        self._yaw_setpoint_list.append(self.yaw_pid.setpoint)
        self._yaw_feedback_list.append(yaw_input)
        self._yaw_output_list.append(yaw_vel)
        self._yaw_output_detail_list.append(self.yaw_pid.components)
        self._fwd_setpoint_list.append(self.fwd_pid.setpoint)
        self._fwd_feedback_list.append(fwd_input)
        self._fwd_output_list.append(fwd_vel)
        self._fwd_output_detail_list.append(self.fwd_pid.components)
        self._time_list.append(time.time() - self._start_time)

        self.last_yaw_vel = (float)(yaw_vel)
        self.last_fwd_vel = (float)(fwd_vel)
        return yaw_vel, fwd_vel


    def reset(self):
        self._yaw_setpoint_list = []
        self._yaw_feedback_list = []
        self._yaw_output_list = []
        self._yaw_output_detail_list = []
        self._fwd_setpoint_list = []
        self._fwd_feedback_list = []
        self._fwd_output_list = []
        self._fwd_output_detail_list = []
        self._time_list = []
        self._start_time = time.time()

        self.last_yaw_vel = 0.0
        self.last_fwd_vel = 0.0
        self.yaw_pid.reset()
        self.fwd_pid.reset()


    @staticmethod
    def is_pid_on(pid: PID):
        return pid.tunings != (0, 0, 0)


    def get_yaw_error(self, p1, p2):
        current = self.__get_yaw_point_from_box(p1, p2)
        return self.yaw_pid.setpoint - current

    def get_fwd_error(self, p1, p2):
        current = self.__get_fwd_point_from_box(p1, p2)
        return self.fwd_pid.setpoint - current

    def get_yaw_data(self):
        return [self._yaw_setpoint_list, self._yaw_feedback_list, self._yaw_output_list]

    def get_yaw_output_detailed(self):
        return list(zip(*self._yaw_output_detail_list))

    def get_fwd_data(self):
        return [self._fwd_setpoint_list, self._fwd_feedback_list, self._fwd_output_list]

    def get_fwd_output_detailed(self):
        return list(zip(*self._fwd_output_detail_list))

    def get_time_data(self, start_at_zero=False):
        if start_at_zero:
            return [t - self._time_list[0] for t in self._time_list]
        return self._time_list

    @staticmethod
    def __get_yaw_point_from_box(p1, p2):
        mid_point = p1 + (p2 - p1) / 2.0
        return mid_point[0]
        
    @staticmethod
    def __get_fwd_point_from_box(p1, p2):
        return (float)(p2[1] - p1[1])

    @staticmethod
    def get_input(p1, p2):
        return (Controller.__get_yaw_point_from_box(p1, p2), Controller.__get_fwd_point_from_box(p1, p2))


##########################################################
###################  TEST  ###############################
##########################################################

def get_points(i):
    center_p1, center_p2 = np.array([0.47568006, 0.50746589]), np.array([0.53723093, 0.86524118])
    left_p1, left_p2 = np.array((0.28849785, 0.52092099)), np.array([0.35023178, 0.87412936])
    right_p1, right_p2 = np.array([0.65865622, 0.51482138]), np.array([0.72162118, 0.87705943])

    if i <= 10 or i > 90:
        return center_p1, center_p2
    elif i <= 50:
        factor = (i - 11) / (50 - 11)
        return interpolate(factor, left_p1, left_p2, center_p1, center_p2)
    elif i <= 90:
        factor = (90 - i) / (90 - 51)
        return interpolate(factor, center_p1, center_p2, right_p1, right_p2)

def interpolate(factor, start_p1, start_p2, end_p1, end_p2):
    int_p1 = (end_p1[0] - start_p1[0]) * factor + start_p1[0]
    int_p2 = (end_p2[0] - start_p2[0]) * factor + start_p2[0]
    return (np.array((int_p1, np.interp(int_p1, [start_p1[0], end_p1[0]], [start_p1[1], end_p1[1]]))),
            np.array((int_p2, np.interp(int_p2, [start_p2[0], end_p2[0]], [start_p2[1], end_p2[1]]))))

if __name__ == "__main__":

    center_p1, center_p2 = np.array([0.47568006, 0.50746589]), np.array([0.53723093, 0.86524118])
    controller = Controller(center_p1, center_p2)

    for i in range(1, 150):
        p1, p2 = get_points(i)
        print(f"Yaw {i}: {controller.control(p1, p2)}")
        time.sleep(0.1)
