from enum import Enum

import cv2
import mediapipe

class Gesture(Enum):
    NO_HAND = 0
    HAND = 1

class tracker():
    def __init__(self):
        self.hand_util = mediapipe.solutions.hands
        self.draw_util = mediapipe.solutions.drawing_utils
        self.hands = self.hand_util.Hands()
        self.landmarks = None

    def get_gesture(self, img):
        results = self.hands.process(img)
        self.landmarks = results.multi_hand_landmarks
        if results.multi_hand_landmarks:
            return Gesture.HAND
        return Gesture.NO_HAND


    def draw_hands(self, img):
        if self.landmarks:
            for handLms in self.landmarks:
                for mark in handLms.landmark:
                    height, width, _ = img.shape
                    cx, cy = int(mark.x * width), int(mark.y * height)
                    cv2.circle(img, (cx, cy), 3, (255, 0, 255), cv2.FILLED)
                self.draw_util.draw_landmarks(img, handLms, self.hand_util.HAND_CONNECTIONS)


def main():
    pass

if __name__ == "__main__":
    main()