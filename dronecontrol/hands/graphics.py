import time
import typing
import cv2
import os
from datetime import datetime
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.hands_connections as mp_connections

from dronecontrol.common import utils
from dronecontrol.hands import gestures
from dronecontrol.common.video_source import *


class HandGui():
    """Provide graphic interface for hand capture.
    
    Class for using video captured from a webcam to detect
    the presence of a hand.
    """
    WIDTH = 640
    HEIGHT = 480
    

    def __init__(self, file=None, max_num_hands=1, log_video=False, source=None):

        self.log = utils.make_stdout_logger(__name__)
        self.__gesture_event_handler = []
        self.__current_time = 0
        self.__past_time = 0
        self.__past_gesture = None

        self.fps = 0
        self.hand_landmarks = None
        self.hand_model = mp_hands.Hands(max_num_hands=max_num_hands)
        self.detector = gestures.Detector()

        self.__source = source if source else HandGui.__get_source(file)
        self.img = self.__source.get_blank()

        self.__video_writer = None
        if log_video:
            self.__video_writer = cv2.VideoWriter(f"img/video_{__name__}_{datetime.now():%d%m%y%H%M%S}.mp4", 
                cv2.VideoWriter_fourcc('M','J','P','G'), 30, self.__source.get_size())


    def close(self):
        cv2.waitKey(1)
        self.__source.close()

        if self.__video_writer:
            self.__video_writer.release()


    def capture(self):
        """Capture image from webcam and extract hand gesture."""
        self.img = self.__source.get_frame()
        if self.__video_writer:
            self.__video_writer.write(self.img)

        results = self.get_landmarks()
        self.hand_landmarks = results.multi_hand_landmarks
        self.hand_landmarks_world = results.multi_hand_world_landmarks

        gesture = self.detector.get_gesture(self.hand_landmarks, results.multi_handedness)
        if gesture is not None and gesture != self.__past_gesture:
            self.__past_gesture = gesture
            self.__invoke_gesture(gesture)


    def render(self, show_fps=True, show_hands=True) -> int:
        """Show captured image in a new window.
        
        Returns a keycode if a key was pressed during rendering
        or -1 if not. 
        """
        self.fps = self.__calculate_fps()

        if show_hands:
            self.draw_hands()
        if show_fps:
            utils.write_text_to_image(self.img, f"FPS: {self.fps}", 0)
        cv2.imshow("Dronecontrol: hand gestures", self.img)
        return cv2.waitKey(self.__source.get_delay())


    def subscribe_to_gesture(self, func: typing.Callable[[gestures.Gesture], None]):
        """Subscribe function to the new gesture event."""
        self.__gesture_event_handler.append(func)


    def unsubscribe_to_gesture(self, func: typing.Callable[[gestures.Gesture], None]):
        """Subscribe function to the new gesture event."""
        self.__gesture_event_handler.remove(func)


    def get_landmarks(self, filepath: str = None) -> typing.NamedTuple:
        """Return landmark solution from image.
        
        Reads the image from a file if given or from the
        last captured image if not."""
        if filepath:
            img = cv2.imread(filepath)
        else:
            img = self.img
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return self.hand_model.process(rgb_img)


    def draw_hands(self, img=None):
        """Draw hand landmarks to captured image."""
        if img is None: 
            img = self.img
        if not self.hand_landmarks:
            return
        for hand in self.hand_landmarks:
            for mark in hand.landmark:
                center = (int(mark.x * self.WIDTH), int(mark.y * self.HEIGHT))
                self.log.debug(f"-> {center[0], center[1]}")
                cv2.circle(img, center, 3, utils.Color.PINK, cv2.FILLED)
            mp_drawing.draw_landmarks(img, hand, mp_connections.HAND_CONNECTIONS)


    def get_current_gesture(self):
        return self.__past_gesture


    @staticmethod
    def __get_source(file):
        if file:
            if os.path.exists(file):
                return FileSource(file)
            else:
                raise FileNotFoundError
        else:
            return CameraSource()


    def __invoke_gesture(self, gesture):
        """Trigger all functions subscribed to new gesture"""
        self.log.info("New gesture: %s", gesture)
        for func in self.__gesture_event_handler:
            func(gesture)


    def __calculate_fps(self) -> int:
        """Calculate FPS from time difference with previous render."""
        self.__current_time = time.perf_counter()
        fps = 1 / (self.__current_time - self.__past_time)
        self.__past_time = self.__current_time
        return int(fps)



if __name__ == "__main__":
    gui = HandGui()
    while True:
        gui.capture()
        if gui.render() > 0:
            break
    
    gui.close()
