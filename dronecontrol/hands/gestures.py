from enum import Enum, IntEnum
import numpy as np
import mediapipe.python.solutions.hands as mediapipe

from dronecontrol.common import utils

class Gesture(Enum):
    NO_HAND = 0
    STOP = 1
    FIST = 2
    BACKHAND = 3
    POINT_UP = 4
    POINT_RIGHT = 5
    POINT_LEFT = 6
    THUMB_RIGHT = 7
    THUMB_LEFT = 8


class Joint(IntEnum):
    FIRST = 0
    MID_LOW = 1
    MID_UP = 2
    TIP = 3


class Finger(IntEnum):
    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    LITTLE = 4


VECTOR_UP = np.array([0, -1, 0])
VECTOR_RIGHT = np.array([1, 0, 0])

# Angle thresholds for detecting the direction a thumb is pointing towards
# depending of if it's the right or the left hand
THUMB_THRESHOLDS = {
    "Right": (85, 120),
    "Left": (65, 100)
}

ZERO_ANGLE = 0
STRAIGHT_ANGLE = 180

EXTENDED_FINGER_THRESHOLD = 50
BACKHAND_THRESHOLD = 40
POINT_RIGHT_THRESHOLD = 60
POINT_LEFT_THRESHOLD = 120


class Detector():
    """Detect hand gestures from joint landmarks."""

    def __init__(self):
        self.log = utils.make_stdout_logger(__name__)


    def get_gesture(self, hands_landmarks, hand_label) -> Gesture:
        """Identify the gesture given by the hand landmarks."""
        self.hands = hands_landmarks
        if self.hands is None:
            return Gesture.NO_HAND
        else:
            self.__process_hand()

        self.label = hand_label[0].classification[0].label
        is_finger_up = self.__get_finger_up_state()
        if not any(is_finger_up[Finger.INDEX:]):
            return Gesture.FIST
        if is_finger_up[Finger.INDEX] and not any(is_finger_up[Finger.MIDDLE:]):
            return self.__get_thumb_index_combination()
        if sum(is_finger_up) == 5:
            if self.__is_backhand():
                return Gesture.BACKHAND
            return Gesture.STOP


    def __process_hand(self):
        """Process landmark array to numpy vector matrices"""
        data = [np.array([p.x, p.y, p.z]) for p in self.hands[0].landmark]
        self.wrist = data[mediapipe.HandLandmark.WRIST]
        self.fingers = np.array(data[1:]).reshape(5, 4, 3)


    def __get_finger_up_state(self):
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
            is_open.append(angle < EXTENDED_FINGER_THRESHOLD)
        return is_open

    
    def __get_thumb_index_combination(self):
        point_gesture = self.__get_point_gesture()
        if point_gesture == Gesture.POINT_UP:
            thumb_gesture = self.__get_thumb_gesture()
            if thumb_gesture:
                return thumb_gesture
        
        return point_gesture


    def __get_point_gesture(self):
        index_vector = self.__get_finger_vector(Finger.INDEX)
        angle = Detector.__angle(index_vector, VECTOR_RIGHT)

        if angle > ZERO_ANGLE and angle < POINT_RIGHT_THRESHOLD:
            return Gesture.POINT_RIGHT
        elif angle > POINT_RIGHT_THRESHOLD and angle < POINT_LEFT_THRESHOLD:
            return Gesture.POINT_UP
        elif angle > POINT_LEFT_THRESHOLD and angle < STRAIGHT_ANGLE:
            return Gesture.POINT_LEFT
        else:
            self.log.error("Could not detect point gesture")


    def __get_thumb_gesture(self):
        thumb_vector = self.__get_finger_vector(Finger.THUMB)
        angle = Detector.__angle(thumb_vector, VECTOR_RIGHT)
        
        if angle > ZERO_ANGLE and angle < THUMB_THRESHOLDS[self.label][0]:
            return Gesture.THUMB_RIGHT
        elif angle > THUMB_THRESHOLDS[self.label][1] and angle < STRAIGHT_ANGLE:
            return Gesture.THUMB_LEFT


    def __is_backhand(self):
        vectors = [self.__get_finger_vector(f) for f in Finger]
        thumb = Detector.__angle(vectors.pop(0), VECTOR_UP)
        others = [Detector.__angle(v, VECTOR_RIGHT) for v in vectors]
        return (thumb < BACKHAND_THRESHOLD and 
            all((x < BACKHAND_THRESHOLD or 
                STRAIGHT_ANGLE - x < BACKHAND_THRESHOLD 
                for x in others)))

    
    def __get_finger_vector(self, finger_name: Finger):
        finger = self.fingers[finger_name]
        return finger[Joint.TIP] - finger[Joint.FIRST]


    @staticmethod
    def __angle(v1, v2):
        """Calculate angle between two vectors."""
        unit_v1 = v1 / np.linalg.norm(v1)
        unit_v2 = v2 / np.linalg.norm(v2)
        rad = np.arccos(np.dot(unit_v1, unit_v2))
        return np.rad2deg(rad)
