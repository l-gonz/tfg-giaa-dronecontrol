import numpy
import cv2
import airsim

from abc import ABC, abstractmethod
from math import tan, pi
from msgpackrpc.error import TimeoutError

from dronecontrol.common import utils

WIDTH = 640
HEIGHT = 480


class VideoSourceEmpty(Exception):
    pass


class VideoSource(ABC):
    def __init__(self) -> None:
        self.__source = None
        self.log = utils.make_stdout_logger(__name__)
        self.img = self.get_blank()

    def get_delay(self):
        return 1

    def get_frame(self):
        return self.get_blank()

    def get_size(self):
        return WIDTH, HEIGHT

    def get_blank(self):
        return numpy.zeros((self.get_size()[1], self.get_size()[0], 3), numpy.uint8)

    @abstractmethod
    def close(self):
        pass


class CameraSource(VideoSource):
    def __init__(self, camera=0):
        self.__source = cv2.VideoCapture(camera)
        super().__init__()
        
        if self.__source.isOpened():
            self.__source.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
            self.__source.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        else:
            self.log.error("Camera video capture failed")
            

    def get_frame(self):
        success, self.img = self.__source.read()
        if not success:
            self.img = self.get_blank()
        else:
            self.img = cv2.flip(self.img, 1)
        return self.img

    def get_size(self):
        if not self.__source.isOpened():
            return WIDTH, HEIGHT
        return int(self.__source.get(3)), int(self.__source.get(4))

    def close(self):
        self.__source.release()
        cv2.destroyAllWindows()


class FileSource(VideoSource):
    def __init__(self, file):
        self.__source = cv2.VideoCapture(file)
        super().__init__()
        if not self.__source.isOpened():
            self.log.error("Could not open video file")

    def get_frame(self):
        if not self.__source.isOpened():
            self.close()
            raise VideoSourceEmpty("Cannot access video file")

        success, self.img = self.__source.read()
        if not success:
            self.img = self.get_blank()
            self.close()
            raise VideoSourceEmpty("Video file finished")

        return cv2.flip(self.img, 1)

    def get_size(self):
        return int(self.__source.get(3)), int(self.__source.get(4))

    def get_delay(self):
        return int(1000 / 60) # 30 frames per second

    def close(self):
        self.__source.release()
        cv2.destroyAllWindows()


class SimulatorSource(VideoSource):
    def __init__(self, ip=""):
        self.height, self.width = 0, 0
        super().__init__()

        self.log.info("Connecting to AirSim for camera source")
        try:
            self.__source = airsim.MultirotorClient(ip, timeout_value=100)
        except TimeoutError:
            self.log.error("AirSim did not respond before timeout")
        self.log.info("AirSim connected")

        self.height, self.width, _ = self.get_frame().shape

    def get_frame(self):
        image = self.__source.simGetImages([
            airsim.ImageRequest("front_center", airsim.ImageType.Scene, False, False)
        ])[0]
        image_bytes = numpy.fromstring(image.image_data_uint8, dtype=numpy.uint8)
        self.img = image_bytes.reshape(image.height, image.width, 3)
        return self.img

    def get_size(self):
        return (self.width, self.height)

    def get_delay(self):
        return 1

    def close(self):
        cv2.destroyAllWindows()
