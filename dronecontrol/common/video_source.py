import numpy
import cv2
import airsim

from abc import ABC, abstractmethod
from math import tan, pi

from dronecontrol.common import utils

try:
    import pyrealsense2
except:
    print("No pyrealsense2 detected, Real Sense SDK will not be available")

WIDTH = 640
HEIGHT = 480


class VideoSourceEmpty(Exception):
    pass


class VideoSource(ABC):
    def __init__(self) -> None:
        self.log = utils.make_stdout_logger(__name__)

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
            img = self.get_blank()
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
            img = self.get_blank()
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


class RealSenseCameraSource(VideoSource):
    def __init__(self):
        super().__init__()
        try:
            self.pipeline = pyrealsense2.pipeline()
        except NameError:
            raise NotImplementedError("Attempted to use RealSense source in a system without Real Sense SDK")
        config = pyrealsense2.config()
        self.pipeline.start(config, self.callback)
        self.image_data = None
        self.valid_data = False

        self.calculate_rectify()
        

    def get_frame(self):
        if self.image_data is None or not self.valid_data:
            return self.get_blank()
        
        self.valid_data = False
        center_undistorted = cv2.remap(src = self.image_data.copy(),
            map1 = self.undistort_rectify[0],
            map2 = self.undistort_rectify[1],
            interpolation = cv2.INTER_LINEAR)
        color_image = cv2.cvtColor(center_undistorted[:,self.max_disp:], cv2.COLOR_GRAY2RGB)
        return color_image

    def get_size(self):
        return (848, 800)

    def close(self):
        try:
            self.pipeline.stop()
        except RuntimeError as e:
            self.log.error(e)

    def callback(self, frame):
        if frame.is_frameset():
            frameset = frame.as_frameset()
            f1 = frameset.get_fisheye_frame(1).as_video_frame()
            self.image_data = numpy.asanyarray(f1.get_data())
            self.valid_data = True

    def calculate_rectify(self):
        min_disp = 0
        num_disp = 112 - min_disp
        self.max_disp = min_disp + num_disp

        profiles = self.pipeline.get_active_profile()
        streams = profiles.get_stream(pyrealsense2.stream.fisheye, 1).as_video_stream_profile()
        intrinsics = streams.get_intrinsics()

        stereo_fov_rad = 90 * (pi/180)  # 90 degree desired fov
        stereo_height_px = 300          # 300x300 pixel stereo output
        stereo_focal_px = stereo_height_px/2 / tan(stereo_fov_rad/2)
        stereo_width_px = stereo_height_px + self.max_disp
        stereo_size = (stereo_width_px, stereo_height_px)
        stereo_cx = (stereo_height_px - 1)/2 + self.max_disp
        stereo_cy = (stereo_height_px - 1)/2

        K_left = RealSenseCameraSource.camera_matrix(intrinsics)
        D_left = RealSenseCameraSource.fisheye_distortion(intrinsics)
        R_left = numpy.eye(3)
        P_left = numpy.array([[stereo_focal_px, 0, stereo_cx, 0],
                       [0, stereo_focal_px, stereo_cy, 0],
                       [0,               0,         1, 0]])
        self.undistort_rectify = cv2.fisheye.initUndistortRectifyMap(K_left, 
            D_left, R_left, P_left, stereo_size, cv2.CV_32FC1)

    def get_extrinsics(src, dst):
        extrinsics = src.get_extrinsics_to(dst)
        R = numpy.reshape(extrinsics.rotation, [3,3]).T
        T = numpy.array(extrinsics.translation)
        return (R, T)

    def camera_matrix(intrinsics):
        return numpy.array([[intrinsics.fx,             0, intrinsics.ppx],
                        [            0, intrinsics.fy, intrinsics.ppy],
                        [            0,             0,              1]])

    def fisheye_distortion(intrinsics):
        return numpy.array(intrinsics.coeffs[:4])
