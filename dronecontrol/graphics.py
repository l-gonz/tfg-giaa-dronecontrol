import time
import logging
import typing

import numpy
import cv2
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.hands_connections as mp_connections

import gestures

class Color():
    """Define color constants to use with cv2."""
    GREEN = (0, 255, 0)
    PINK = (255, 0, 255)


class HandGui():
    """Provide graphic interface for hand capture.
    
    Class for using video captured from a webcam to detect
    the presence of a hand.
    """
    FONT = cv2.FONT_HERSHEY_PLAIN
    IMAGE_SCALE = 1.5
    FONT_SCALE = 2
    WIDTH = 640
    HEIGHT = 480
    
    __current_time = 0
    __past_time = 0
    __past_gesture = gestures.Gesture.NO_HAND
    __gesture_event_handler = []
    img = None
    fps = 0
    hand_landmarks = None

    def __init__(self, max_num_hands=1):
        self.__capture = cv2.VideoCapture(0)
        self.hand_model = mp_hands.Hands(max_num_hands=max_num_hands)

        if self.__capture.isOpened():
            self.__capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
            self.__capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)
        else:
            logging.error("Cannot access camera")


    def capture(self):
        """Capture image from webcam and extract hand landmarks."""
        success, self.img = self.__capture.read()
        if not success:
            self.img = numpy.zeros((self.HEIGHT, self.WIDTH, 3), numpy.uint8)

        rgb_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        results = self.hand_model.process(rgb_img)

        self.hand_landmarks = results.multi_hand_landmarks
        self.hand_landmarks_world = results.multi_hand_world_landmarks

        detector = gestures.Detector(self.hand_landmarks)
        gesture = detector.get_gesture()
        if gesture != self.__past_gesture:
            self.__past_gesture = gesture
            self.__invoke_gesture(gesture)


    def render(self, show_fps=True, show_hands=True) -> int:
        """Show captured image in a new window.
        
        Returns a keycode if a key was pressed during rendering
        or -1 if not. 
        """
        self.fps = self.__calculate_fps()

        if show_hands:
            self.__draw_hands()
        if show_fps:
            self.annotate(f"FPS: {self.fps}", 0)
        cv2.imshow("Image", self.img)
        return cv2.waitKey(1)


    def annotate(self, value, channel=1):
        """Annotate the captured image with the given text.
        
        Several channels available for positioning the text."""
        cv2.putText(self.img, str(value),
            self.__get_text_pos(channel),
            self.FONT, self.FONT_SCALE, Color.GREEN, self.FONT_SCALE)


    def subscribe_to_gesture(self, func: function):
        """Subscribe function to the new gesture event."""
        self.__gesture_event_handler.append(func)


    def __invoke_gesture(self, gesture):
        """Trigger all functions subscribed to new gesture"""
        for func in self.__gesture_event_handler:
            func(gesture)


    def __draw_hands(self):
        """Draw hand landmarks to captured image."""
        if not self.hand_landmarks:
            return
        for hand in self.hand_landmarks:
            for mark in hand.landmark:
                center = (int(mark.x * self.WIDTH), int(mark.y * self.HEIGHT))
                self.log.debug(f"-> {center[0], center[1]}")
                cv2.circle(self.img, center, 3, Color.PINK, cv2.FILLED)
            mp_drawing.draw_landmarks(self.img, hand, mp_connections.HAND_CONNECTIONS)


    def __calculate_fps(self) -> int:
        """Calculate FPS from time difference with previous render."""
        self.__current_time = time.perf_counter()
        fps = 1 / (self.__current_time - self.__past_time)
        self.__past_time = self.__current_time
        return int(fps)


    def __get_text_pos(self, channel) -> typing.Tuple[int,int]:
        """Map channel number to pixel position."""
        if channel == 0:
            return (10, 30)
        if channel == 1:
            return (10, self.HEIGHT - 10)
        if channel == 2:
            return (10, self.HEIGHT - 50)


def main():
    cam = HandGui()
    # while True:
    cam.capture()
    cam.annotate("Drone: Take-off", 1)
    cam.annotate("Hand: detected", 2)
    cam.render()

    cv2.waitKey(1)
        # if cv2.waitKey(1) >= 0:
        #     break


if __name__ == "__main__":
    main()
