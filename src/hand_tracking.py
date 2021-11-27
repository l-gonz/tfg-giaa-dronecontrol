from enum import Enum
import logging

import numpy
import cv2
import mediapipe
from tensorflow.keras.models import load_model

import camera

class Gesture(Enum):
    NO_HAND = 0
    HAND = 1

class tracker():
    def __init__(self):
        self.hand_util = mediapipe.solutions.hands
        self.draw_util = mediapipe.solutions.drawing_utils
        self.hands = self.hand_util.Hands(max_num_hands=1)
        self.landmarks = None

        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
        self.log.addHandler(handler)

        self.load_model()


    def load_model(self):
        # Load the gesture recognizer model
        self.model = load_model('Firmware/hand-gesture-recognition-code/mp_hand_gesture')

        # Load class names
        with open('Firmware/hand-gesture-recognition-code/gesture.names', 'r') as file:
            self.gestures = file.read().split('\n')
        self.log.info(self.gestures)


    def get_gesture(self, img):
        results = self.hands.process(img)
        self.landmarks = results.multi_hand_landmarks

        height, width, _ = img.shape
        if results.multi_hand_landmarks:
            landmarks = []
            for handslms in results.multi_hand_landmarks:
                for lm in handslms.landmark:
                    lmx = int(lm.x * width)
                    lmy = int(lm.y * height)
                    landmarks.append([lmx, lmy])
                prediction = self.model.predict([landmarks])
                logging.info(prediction)
                gesture = self.gestures[numpy.argmax(prediction)]
                return gesture

        #     return Gesture.HAND
        # return Gesture.NO_HAND


    def draw_hands(self, img):
        if self.landmarks:
            for handLms in self.landmarks:
                for mark in handLms.landmark:
                    height, width, _ = img.shape
                    cx, cy = int(mark.x * width), int(mark.y * height)
                    cv2.circle(img, (cx, cy), 3, (255, 0, 255), cv2.FILLED)
                self.draw_util.draw_landmarks(img, handLms, self.hand_util.HAND_CONNECTIONS)


def main():
    gui = camera.handler()
    hand = tracker()
    while True:
        img = gui.capture()

        gesture = hand.get_gesture(img)
        hand.draw_hands(gui.img)
        gui.annotate(f"Detect: {gesture}", 1)
        gui.render()

        # Check for loop end
        if gui.is_exit():
            break

if __name__ == "__main__":
    main()