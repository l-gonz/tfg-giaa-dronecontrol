from dronecontrol.follow.pid import PID

import numpy as np
import time

class Controller:

    MAX_FWD_VEL = 1
    MAX_YAW_VEL = 5
    MAX_HEIGHT_VARIANCE = 2
    ALLOWED_ERROR = 0.02
    ZEROES = np.asarray([0, 0])
    ONES = np.asarray([1, 1])

    def __init__(self, target_x, target_height) -> None:
        self.yaw_pid = PID(115, 0.16, 60)
        self.fwd_pid = PID(7, 0.01, 0.03)
        
        self.yaw_pid.setSampleTime(0.01)
        self.fwd_pid.setSampleTime(0.01)

        self.yaw_pid.SetPoint = target_x
        self.fwd_pid.SetPoint = target_height
        self.prev_fwd_feedback = target_height

        self.reset()

    
    def control(self, p1, p2):
        if np.array_equal(p1, self.ZEROES) and np.array_equal(p2, self.ONES):
            return 0, 0

        yaw_input = self.__get_yaw_point_from_box(p1, p2)
        self.yaw_pid.update(yaw_input)
        yaw_vel = self.__get_yaw_vel_from_output(self.yaw_pid.output)

        fwd_input = self.__get_fwd_point_from_box(p1, p2)
        self.fwd_pid.update(fwd_input)
        fwd_vel = self.__get_fwd_vel_from_output(self.fwd_pid.output)

        self._yaw_setpoint_list.append(self.yaw_pid.SetPoint)
        self._yaw_feedback_list.append(yaw_input)
        self._yaw_output_list.append(yaw_vel)
        self._fwd_setpoint_list.append(self.fwd_pid.SetPoint)
        self._fwd_feedback_list.append(fwd_input)
        self._fwd_output_list.append(fwd_vel)
        self._time_list.append(self.yaw_pid.current_time - self._start_time)

        # Stop control when close enough
        # if abs(1 - yaw_input / self.yaw_pid.SetPoint) < self.ALLOWED_ERROR:
        #     yaw_vel = 0
        # if abs(1 - fwd_input / self.fwd_pid.SetPoint) < self.ALLOWED_ERROR:
        #     fwd_vel = 0

        self.last_yaw_vel = yaw_vel
        self.last_fwd_vel = fwd_vel
        return yaw_vel, fwd_vel


    def reset(self):
        self._yaw_setpoint_list = []
        self._yaw_feedback_list = []
        self._yaw_output_list = []
        self._fwd_setpoint_list = []
        self._fwd_feedback_list = []
        self._fwd_output_list = []
        self._time_list = []
        self._start_time = time.time()

        self.last_yaw_vel = 0
        self.last_fwd_vel = 0

    
    def set_yaw_gains(self, kp, ki, kd):
        self.yaw_pid.setKp(kp)
        self.yaw_pid.setKi(ki)
        self.yaw_pid.setKd(kd)
    

    def set_fwd_gains(self, kp, ki, kd):
        self.fwd_pid.setKp(kp)
        self.fwd_pid.setKi(ki)
        self.fwd_pid.setKd(kd)


    def get_yaw_error(self, p1, p2):
        current = self.__get_yaw_point_from_box(p1, p2)
        return self.yaw_pid.SetPoint - current

    def get_fwd_error(self, p1, p2):
        current = self.__get_fwd_point_from_box(p1, p2)
        return self.fwd_pid.SetPoint - current

    def get_yaw_data(self):
        return [self._yaw_setpoint_list, self._yaw_feedback_list, self._yaw_output_list]

    def get_fwd_data(self):
        return [self._fwd_setpoint_list, self._fwd_feedback_list, self._fwd_output_list]

    def get_time_data(self, start_at_zero=False):
        if start_at_zero:
            return [t - self._time_list[0] for t in self._time_list]
        return self._time_list

    
    def __get_yaw_point_from_box(self, p1, p2):
        mid_point = p1 + (p2 - p1) / 2
        return mid_point[0]
        

    def __get_fwd_point_from_box(self, p1, p2):
        height = p2[1] - p1[1]

        # Smooth input to adjust for sudden changes in detected height
        # that differ greatly from the target height
        error = height - self.fwd_pid.SetPoint
        diff = height - self.prev_fwd_feedback
        if error > self.MAX_HEIGHT_VARIANCE and diff > self.MAX_HEIGHT_VARIANCE:
            input = self.fwd_pid.SetPoint + self.MAX_HEIGHT_VARIANCE
        elif error < -self.MAX_HEIGHT_VARIANCE and diff < -self.MAX_HEIGHT_VARIANCE:
            input = self.fwd_pid.SetPoint - self.MAX_HEIGHT_VARIANCE
        else:
            input = height
        self.prev_fwd_feedback = input
        
        return input


    def __get_yaw_vel_from_output(self, output):
        clipped = np.clip(-output, -self.MAX_YAW_VEL, self.MAX_YAW_VEL)
        return clipped


    def __get_fwd_vel_from_output(self, output):
        clipped = np.clip(output, -self.MAX_FWD_VEL, self.MAX_FWD_VEL)
        return clipped


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
