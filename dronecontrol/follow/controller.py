from dronecontrol.follow.pid import PID

import numpy as np
import time
import matplotlib.pyplot as plt

class Controller:

    MAX_FWD_VEL = 1
    MAX_YAW_VEL = 6
    MAX_AREA_VARIANCE = 2
    ZEROES = np.asarray([0, 0])
    ONES = np.asarray([1, 1])

    def __init__(self, target_x, area_percentage) -> None:
        self.yaw_pid = PID(40, 5, 1)
        self.fwd_pid = PID(.5, .08, 0.001)
        
        self.yaw_pid.setSampleTime(0.01)
        self.fwd_pid.setSampleTime(0.01)

        self.yaw_pid.SetPoint = target_x
        self.fwd_pid.SetPoint = area_percentage
        self.prev_fwd_feedback = area_percentage

        self._feedback_list = []
        self._time_list = []
        self._setpoint_list = []
        self._output_list = []
        self._start_time = time.time()

    
    def control(self, p1, p2):
        if np.array_equal(p1, self.ZEROES) and np.array_equal(p2, self.ONES):
            return 0, 0

        self.yaw_pid.update(self.__get_yaw_point_from_box(p1, p2))
        yaw_vel = self.__get_yaw_vel_from_output(self.yaw_pid.output)

        self.fwd_pid.update(self.__get_fwd_point_from_box(p1, p2))
        fwd_vel = self.__get_fwd_vel_from_output(self.fwd_pid.output)

        self._feedback_list.append(self.__get_fwd_point_from_box(p1, p2))
        self._setpoint_list.append(self.fwd_pid.SetPoint)
        self._time_list.append(self.fwd_pid.current_time - self._start_time)
        self._output_list.append(fwd_vel)
        
        return yaw_vel, fwd_vel


    def plot(self):
        if len(self._time_list) == 0:
            return

        plt.plot(self._time_list, self._feedback_list)
        plt.plot(self._time_list, self._setpoint_list)
        plt.plot(self._time_list, self._output_list)

        plt.xlim((0, self._time_list[-1]))
        min_y = min(self._output_list + self._feedback_list)-0.2
        max_y = max(self._output_list + self._feedback_list)+0.2
        plt.ylim((min_y, max_y))
        plt.xlabel('time (s)')
        plt.ylabel('PID (PV)')
        plt.title('TEST PID')

        plt.grid(True)
        plt.show()

    
    def __get_yaw_point_from_box(self, p1, p2):
        mid_point = p1 + (p2 - p1) / 2
        return mid_point[0]
        

    def __get_fwd_point_from_box(self, p1, p2):
        area = (p2[0] - p1[0]) * (p2[1] - p1[1]) * 100

        # Adjust for sudden changes in detected area that differ greatly from the target area
        error = area - self.fwd_pid.SetPoint
        diff = area - self.prev_fwd_feedback
        if error > self.MAX_AREA_VARIANCE and diff > self.MAX_AREA_VARIANCE:
            input = self.fwd_pid.SetPoint + self.MAX_AREA_VARIANCE
        elif error < -self.MAX_AREA_VARIANCE and diff < -self.MAX_AREA_VARIANCE:
            input = self.fwd_pid.SetPoint - self.MAX_AREA_VARIANCE
        else:
            input = area
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
