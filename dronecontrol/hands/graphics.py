import time
import typing
import cv2
import os
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.hands_connections as mp_connections

from dronecontrol import utils
from dronecontrol.hands import gestures
from dronecontrol.video_source import CameraSource, FileSource, VideoSource

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
    FONT_SCALE = 2
    WIDTH = 640
    HEIGHT = 480
    

    def __init__(self, file=None, max_num_hands=1):

        self.log = utils.make_logger(__name__)
        self.__gesture_event_handler = []
        self.__current_time = 0
        self.__past_time = 0
        self.__past_gesture = None

        self.fps = 0
        self.hand_landmarks = None
        self.hand_model = mp_hands.Hands(max_num_hands=max_num_hands)

        self.__source = self.__get_source(file)
        self.img = VideoSource.get_blank()


    def capture(self):
        """Capture image from webcam and extract hand gesture."""
        self.img = self.__source.get_frame()

        results = self.get_landmarks()
        self.hand_landmarks = results.multi_hand_landmarks
        self.hand_landmarks_world = results.multi_hand_world_landmarks

        detector = gestures.Detector(self.hand_landmarks)
        gesture = detector.get_gesture()
        if gesture is not None and gesture != self.__past_gesture:
            self.__past_gesture = gesture
            self.__invoke_gesture(gesture)


    def render(self, show_fps=True, show_hands=True, delay=1) -> int:
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
        return cv2.waitKey(delay)


    def annotate(self, value, channel=1):
        """Annotate the captured image with the given text.
        
        Several channels available for positioning the text."""
        cv2.putText(self.img, str(value),
            self.__get_text_pos(channel),
            self.FONT, self.FONT_SCALE, Color.GREEN, self.FONT_SCALE)


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
