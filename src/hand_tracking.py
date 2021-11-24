import time
from enum import Enum

import mediapipe as mp

class Gesture(Enum):
    FIST = 1

class tracker():
    def __init__(self):
        mpHands = mp.solutions.hands
        # mpDraw = mp.solutions.drawing_utils
        self.hands = mpHands.Hands()

    def get_gesture(self, img):
        results = self.hands.process(img)
        # print("Hand:", "found" if results.multi_hand_landmarks else "not found")
        if results.multi_hand_landmarks:
            return Gesture.FIST
        return 0

        # if results.multi_hand_landmarks:
        #     for handLms in results.multi_hand_landmarks:
        #         for id, lm in enumerate(handLms.landmark):
        #             #print(id,lm)
        #             h, w, c = img.shape
        #             cx, cy = int(lm.x * w), int(lm.y * h)
        #             #if id ==0:
        #             cv2.circle(img, (cx,cy), 3, (255,0,255), cv2.FILLED)
        #         mpDraw.draw_landmarks(img, handLms, mpHands.HAND_CONNECTIONS)


def main():
    pass

if __name__ == "__main__":
    main()