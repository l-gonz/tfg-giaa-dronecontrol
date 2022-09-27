import os
import datetime
import time
import cv2
import asyncio
from enum import Enum
import mediapipe as mp

from dronecontrol.common import utils, pilot
from dronecontrol.common.video_source import CameraSource, SimulatorSource, RealSenseCameraSource, FileSource
from dronecontrol.hands.graphics import HandGui
from dronecontrol.follow.image_processing import detect


mp_pose = mp.solutions.pose


class CameraMode(Enum):
    PICTURE = 0
    VIDEO = 1

class ImageDetection(Enum):
    NONE = 0
    HAND = 1
    POSE = 2

class VideoCamera:
    IMAGE_FOLDER = 'img'
    VIDEO_CODE = cv2.VideoWriter_fourcc('M','J','P','G')

    def __init__(self, use_simulator, use_hardware, use_wsl, use_realsense, 
                 image_detection, hardware_address=None, simulator_ip=None,
                 file=None):
        self.log = utils.make_stdout_logger(__name__)
        self.pilot = None
        if use_simulator or use_hardware:
            self.pilot = pilot.System(use_serial=use_hardware, serial_address=hardware_address)

        if use_realsense:
            self.source = RealSenseCameraSource()
        elif file:
            self.source = FileSource(file)
        elif use_simulator:
            self.source = SimulatorSource(utils.get_wsl_host_ip() if use_wsl else simulator_ip if simulator_ip else "")
        else:
            self.source = CameraSource()
        self.img = self.source.get_blank()

        self.mode = CameraMode.PICTURE
        self.is_recording = False
        self.out = None
        self.last_run_time = time.time()

        self.hand_detection = HandGui(source = self.source) if image_detection == ImageDetection.HAND else None
        self.pose_detection = mp_pose.Pose(model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5) if image_detection == ImageDetection.POSE else None
        

    async def run(self):
        pilot_task = asyncio.create_task(self.pilot.start()) if self.pilot else None
        
        while True:
            if self.hand_detection:
                self.hand_detection.capture()
                raw_img = self.hand_detection.img
                self.img = raw_img.copy()
                self.hand_detection.draw_hands()
            else:
                raw_img = self.source.get_frame()
                self.img = raw_img.copy()

                if self.pose_detection:
                    results = self.pose_detection.process(self.img)
                    detect(results, raw_img)

            utils.write_text_to_image(raw_img, f"Mode {self.mode}: {'' if self.is_recording else 'not '} recording", 0)
            utils.write_text_to_image(raw_img, f"FPS: {round(1.0 / (time.time() - self.last_run_time))}")
            self.last_run_time = time.time()
            cv2.imshow("Image", raw_img)

            try:
                self.__handle_key_input()
            except KeyboardInterrupt:
                break

            if self.is_recording:
                self.out.write(self.img)
            
            if pilot_task and pilot_task.done():
                break
            
            await asyncio.sleep(1 / 30)

        if pilot_task:
            if not pilot_task.done():
                pilot_task.cancel()
            try:
                await pilot_task
            except Exception as e:
                self.log.error(e)

        
    def close(self):
        cv2.waitKey(1)
        if self.out:
            self.out.release()
        self.source.close()
        if self.pilot:
            self.pilot.close()

        if self.pose_detection:
            self.pose_detection.close()


    def change_mode(self):
        if self.mode == CameraMode.VIDEO and self.is_recording:
            self.trigger()

        self.mode = CameraMode((self.mode.value + 1) % len(CameraMode))

    
    def trigger(self):
        if self.mode == CameraMode.PICTURE:
            self.__write_image()
        elif self.mode == CameraMode.VIDEO:
            if self.is_recording:
                self.out.release()
                self.out = None
            else:
                self.out = self.__write_video()
            self.is_recording = not self.is_recording


    def __handle_key_input(self):
        key_action = utils.keyboard_control(cv2.waitKey(self.source.get_delay()))
        if key_action is None:
            pass
        elif self.pilot and pilot.System.__name__ in key_action.__qualname__:
            self.pilot.queue_action(key_action, interrupt=True)
        elif VideoCamera.__name__ in key_action.__qualname__:
            key_action(self)


    def __write_image(self, filepath: str=None):
        """Save current captured image to file."""
        if not filepath:
            if not os.path.exists(VideoCamera.IMAGE_FOLDER):
                os.makedirs(VideoCamera.IMAGE_FOLDER)
            filepath = f"{VideoCamera.IMAGE_FOLDER}/{VideoCamera.__get_formatted_date()}.jpg"
        cv2.imwrite(filepath, self.img)


    def __write_video(self):
        if not os.path.exists(VideoCamera.IMAGE_FOLDER):
            os.makedirs(VideoCamera.IMAGE_FOLDER)
        filepath = f"{VideoCamera.IMAGE_FOLDER}/{VideoCamera.__get_formatted_date()}.avi"
        return cv2.VideoWriter(filepath, VideoCamera.VIDEO_CODE, 30, self.source.get_size())
    

    @staticmethod
    def __get_formatted_date():
        return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
