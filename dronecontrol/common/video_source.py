from abc import ABC, abstractmethod
import numpy
import cv2

from dronecontrol.common import utils

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

    @abstractmethod
    def get_size(self):
        pass

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

    def get_size(self):
        return int(self.__source.get(3)), int(self.__source.get(4))

    def close(self):
        self.__source.release()


class FileSource(VideoSource):
    def __init__(self, file):
        super().__init__()
        self.__source = cv2.VideoCapture(file)
        if not self.__source.isOpened():
            self.log.error("Could not open video file")

    def get_frame(self):
        if not self.__source.isOpened():
            self.close()
            raise VideoSourceEmpty("Cannot access video file")

        success, img = self.__source.read()
        if not success:
            img = CameraSource.get_blank()
            self.close()
            raise VideoSourceEmpty("Video file finished")

        return img

    def get_size(self):
        return int(self.__source.get(3)), int(self.__source.get(4))

    def close(self):
        self.__source.release()


class SimulatorSource(VideoSource):
    pass
