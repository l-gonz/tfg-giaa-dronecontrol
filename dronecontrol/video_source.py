from abc import ABC, abstractmethod
from os import get_blocking
import numpy
import cv2

from dronecontrol import utils

WIDTH = 640
HEIGHT = 480


class VideoSourceEmpty(Exception):
    pass


class VideoSource(ABC):
    def __init__(self) -> None:
        self.log = utils.make_logger(__name__)

    @abstractmethod
    def get_frame(self):
        return VideoSource.get_blank()

    @staticmethod
    def get_blank():
        return numpy.zeros((HEIGHT, WIDTH, 3), numpy.uint8)


class CameraSource(VideoSource):
    def __init__(self, camera=0):
        super().__init__()
        self.__source = cv2.VideoCapture(camera)
        
        if self.__source.isOpened():
            self.__source.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
            self.__source.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        else:
            self.log.error("Camera video capture failed")

    def get_frame(self):
        success, img = self.__source.read()
        if not success:
            img = CameraSource.get_blank()
            raise VideoSourceEmpty("Cannot access camera")

        img = cv2.flip(img, 1)
        return img


class FileSource(VideoSource):
    def __init__(self, file):
        super().__init__()
        self.__source = cv2.VideoCapture(file)
        if not self.__source.isOpened():
            self.log.error("Could not open video file")

    def get_frame(self):
        if self.__source.isOpened():
            success, img = self.__source.read()
            if not success:
                img = CameraSource.get_blank()
                raise VideoSourceEmpty("Cannot access video file")
        else:
            self.__source.release()
            raise VideoSourceEmpty("Video file finished")

        return img
