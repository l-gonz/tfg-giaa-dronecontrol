from enum import Enum
import numpy as np

import cv2
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.hands_connections as mp_connections

import camera

class Gesture(Enum):
    NO_HAND = 0
    STOP = 1
    FIST = 2

class tracker():
    def __init__(self):
        self.hand_model = mp_hands.Hands(max_num_hands=1)
        self.hands = None


    def get_gesture(self, img):
        results = self.hand_model.process(img)
        self.hands = results.multi_hand_landmarks
        if self.hands is None:
            return Gesture.NO_HAND

        self.process_hand()
        fingers = self.__get_fingers()
        if fingers == 0:
            return Gesture.FIST
        if fingers == 5:
            return Gesture.STOP


    def process_hand(self):
        data = [np.array([p.x, p.y, p.z]) for p in self.hands[0].landmark]
        self.wrist = data[mp_hands.HandLandmark.WRIST]
        self.fingers = np.array(data[1:]).reshape(5, 4, 3)


    def __get_fingers(self):
        # Calculate two vectors per finger
        # One from wrist to first point, second from first point to last
        is_open = []
        for finger in self.fingers:
            base = finger[0] - self.wrist
            tip = finger[3] - finger[0]
            angle = tracker.__angle(base, tip)
            is_open.append(angle < 50)
        return sum(is_open)


    @staticmethod
    def __angle(v1, v2):
        unit_v1 = v1 / np.linalg.norm(v1)
        unit_v2 = v2 / np.linalg.norm(v2)
        rad = np.arccos(np.dot(unit_v1, unit_v2))
        return np.rad2deg(rad)


    def draw_hands(self, img):
        if not self.hands:
            return
        for handLms in self.hands:
            for mark in handLms.landmark:
                height, width, _ = img.shape
                cx, cy = int(mark.x * width), int(mark.y * height)
                cv2.circle(img, (cx, cy), 3, (255, 0, 255), cv2.FILLED)
            mp_drawing.draw_landmarks(img, handLms, mp_connections.HAND_CONNECTIONS)


def main():
    gui = camera.handler()
    hand = tracker()

    # while True:
    img = gui.capture()
    gesture = hand.get_gesture(img)
    hand.draw_hands(gui.img)
    gui.annotate(str(gesture), 1)
    gui.render()

    gui.is_exit()

if __name__ == "__main__":
    main()