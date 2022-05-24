from abc import ABC, abstractmethod
import numpy
import cv2
import airsim

from dronecontrol.common import utils

WIDTH = 640
HEIGHT = 480


class VideoSourceEmpty(Exception):
    pass


class VideoSource(ABC):
    def __init__(self) -> None:
        self.log = utils.make_stdout_logger(__name__)

    def get_delay(self):
        return 1

    @abstractmethod
    def get_frame(self):
        return VideoSource.get_blank()

    @abstractmethod
    def get_size(self):
        pass

    @abstractmethod
    def close(self):
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
        else:
            img = cv2.flip(img, 1)
        return img

    def get_size(self):
        if not self.__source.isOpened():
            return WIDTH, HEIGHT
        return int(self.__source.get(3)), int(self.__source.get(4))

    def close(self):
        self.__source.release()
        cv2.destroyAllWindows()


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

        return cv2.flip(img, 1)

    def get_size(self):
        return int(self.__source.get(3)), int(self.__source.get(4))

    def get_delay(self):
        return int(1000 / 60) # 30 frames per second

    def close(self):
        self.__source.release()
        cv2.destroyAllWindows()


class SimulatorSource(VideoSource):
    def __init__(self, ip=""):
        super().__init__()
        self.__source = airsim.MultirotorClient(ip)

    def get_frame(self):
        image = self.__source.simGetImages([
            airsim.ImageRequest("front_center", airsim.ImageType.Scene, False, False)
        ])[0]
        image_bytes = numpy.fromstring(image.image_data_uint8, dtype=numpy.uint8)
        return image_bytes.reshape(image.height, image.width, 3)

    def get_size(self):
        return (1280, 800)

    def get_delay(self):
        return int(1000/60)

    def close(self):
        cv2.destroyAllWindows()
