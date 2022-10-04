from enum import Enum
import numpy as np
import mediapipe.python.solutions.hands as mediapipe

from dronecontrol.common import utils

class Gesture(Enum):
    NO_HAND = 0
    STOP = 1
    FIST = 2
    POINT_UP = 3
    POINT_RIGHT = 4
    POINT_LEFT = 5
    THUMB_RIGHT = 6
    THUMB_LEFT = 7


class Joint():
    FIRST = 0
    MID_LOW = 1
    MID_UP = 2
    TIP = 3


class FINGER():
    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    LITTLE = 4


VECTOR_UP = np.array([1, 0, 0])


class Detector():
    """Detect hand gestures from joint landmarks."""
    EXTENDED_FINGER_THRESHOLD = 50

    def __init__(self, hands_landmarks):
        self.log = utils.make_stdout_logger(__name__)
        self.hands = hands_landmarks
        if self.hands != None:
            self.__process_hand()


    def get_gesture(self) -> Gesture:
        """Identify the gesture given by the hand landmarks."""
        if self.hands == None:
            return Gesture.NO_HAND

        finger_state = self.__get_finger_state()
        if sum(finger_state) == 0:
            return Gesture.FIST
        if not any(finger_state[FINGER.MIDDLE:]):
            return self.__get_thumb_index_combination()
        if sum(finger_state) == 5:
            return Gesture.STOP


    def __process_hand(self):
        """Process landmark array to numpy vector matrices"""
        data = [np.array([p.x, p.y, p.z]) for p in self.hands[0].landmark]
        self.wrist = data[mediapipe.HandLandmark.WRIST]
        self.fingers = np.array(data[1:]).reshape(5, 4, 3)


    def __get_finger_state(self):
        """Return a list with the status of each finger
        of whether it is extended or not.
        
        Checks that the angle between a vector drawn from 
        the wrist to the first point and one from 
        the first point to the tip is small enough."""
        is_open = []
        for finger in self.fingers:
            base = finger[Joint.FIRST] - self.wrist
            tip = finger[Joint.TIP] - finger[Joint.FIRST]
            angle = Detector.__angle(base, tip)
            is_open.append(angle < self.EXTENDED_FINGER_THRESHOLD)
        return is_open

    
    def __get_thumb_index_combination(self):
        point_gesture = self.__get_point_gesture()
        if point_gesture == Gesture.POINT_UP:
            thumb_gesture = self.__get_thumb_gesture()
            if thumb_gesture:
                return thumb_gesture
        
        return point_gesture


    def __get_point_gesture(self):
        index = self.fingers[FINGER.INDEX]
        index_vector = index[Joint.TIP] - index[Joint.FIRST]
        angle = Detector.__angle(index_vector, VECTOR_UP)

        if angle > 0 and angle < 70:
            return Gesture.POINT_RIGHT
        elif angle > 70 and angle < 110:
            return Gesture.POINT_UP
        elif angle > 110 and angle < 180:
            return Gesture.POINT_LEFT
        else:
            self.log.error("Could not detect point gesture")


    def __get_thumb_gesture(self):
        thumb = self.fingers[FINGER.THUMB]
        thumb_vector = thumb[Joint.TIP] - thumb[Joint.FIRST]
        angle = Detector.__angle(thumb_vector, VECTOR_UP)
        
        if angle > 0 and angle < 80:
            return Gesture.THUMB_RIGHT
        elif angle > 100 and angle < 180:
            return Gesture.THUMB_LEFT


    @staticmethod
    def __angle(v1, v2):
        """Calculate angle between two vectors."""
        unit_v1 = v1 / np.linalg.norm(v1)
        unit_v2 = v2 / np.linalg.norm(v2)
        rad = np.arccos(np.dot(unit_v1, unit_v2))
        return np.rad2deg(rad)
