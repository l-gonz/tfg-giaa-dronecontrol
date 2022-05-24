import os
import datetime
import traceback
import cv2
import asyncio
from enum import Enum

from dronecontrol.common import utils, pilot
from dronecontrol.common.video_source import CameraSource, SimulatorSource

class CameraMode(Enum):
    PICTURE = 0
    VIDEO = 1

class VideoCamera:
    IMAGE_FOLDER = 'img'
    VIDEO_CODE = cv2.VideoWriter_fourcc('M','J','P','G')

    def __init__(self, use_simulator, use_hardware, use_wsl) -> None:
        self.log = utils.make_stdout_logger(__name__)
        self.pilot = None
        if use_simulator or use_hardware:
            self.pilot = pilot.System(use_serial=use_hardware)

        if use_simulator and use_wsl:
            self.source = SimulatorSource(utils.get_wsl_host_ip())
        else:
            self.source = CameraSource()
        self.img = self.source.get_blank()

        self.mode = CameraMode.PICTURE
        self.is_recording = False
        self.out = None
        

    async def run(self):
        self.pilot_task = asyncio.create_task(self.pilot.start())
        
        while True:
            self.img = self.source.get_frame()

            try:
                key_action = utils.keyboard_control(cv2.waitKey(self.source.get_delay()))
                if key_action is None:
                    pass
                elif self.pilot and pilot.System.__name__ in key_action.__qualname__:
                    self.pilot.queue_action(key_action, interrupt=True)
                elif VideoCamera.__name__ in key_action.__qualname__:
                    key_action(self)
            except KeyboardInterrupt:
                break

            if self.is_recording:
                self.out.write(self.img)
            
            if self.pilot_task.done():
                break
            
            cv2.putText(self.img, f"Mode {self.mode}: {'' if self.is_recording else 'not '} recording",
                (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
            cv2.imshow("Image", self.img)
            await asyncio.sleep(1 / 30)

        if not self.pilot_task.done():
            self.pilot_task.cancel()
        await self.pilot_task

        
    def close(self):
        cv2.waitKey(1)
        if self.out:
            self.out.release()
        self.source.close()
        self.pilot.close()


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



def test_camera(use_simulator, use_hardware, use_wsl):
    log = utils.make_stdout_logger(__name__)
    camera = VideoCamera(use_simulator, use_hardware, use_wsl)
    try:
        asyncio.run(camera.run())
    except asyncio.CancelledError:
        log.warning("Cancel program run")
    except KeyboardInterrupt:
        log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
    finally:
        camera.close()


if __name__ == "__main__":
    test_camera(False, False, False)
