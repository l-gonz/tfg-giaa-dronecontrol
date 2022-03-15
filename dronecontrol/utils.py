import logging
import cv2
import os
import datetime

from dronecontrol.video_source import CameraSource

LOGGING_FORMAT = '%(levelname)s:%(name)s: %(message)s'

def make_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Return a dedicated logger for a module."""
    log = logging.getLogger(name)
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    log.addHandler(handler)
    return log


def save_image(self, img, filepath: str=None):
    """Save current captured image to file."""
    if not filepath:
        if not os.path.exists('img'):
            os.makedirs('img')
        filepath = "img/" + datetime.datetime.now().strftime("%Y%m%d-%h%m%s") + ".jpg"
    cv2.imwrite(filepath, img)


def take_images():
    """Run a graphic interface where images can
    be saved using the Space key.
    
    Quit with 'q'."""
    source = CameraSource()
    while True:
        img = source.get_frame()
        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        if key == ord(" "):
            save_image(img)

        cv2.putText(img, "SPACE to take picture\n'q' to exit",
            (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.imshow("Image", img)


def take_video():
    source = CameraSource()
    frame_width = int(source.get(3))
    frame_height = int(source.get(4))
    is_recording = False
    
    while True:
        img = source.get_frame()
        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        if key == ord(" "):
            if is_recording:
                out.release()
            else:
                out = cv2.VideoWriter('img/outpy.avi', cv2.VideoWriter_fourcc('M','J','P','G'), 
                            10, (frame_width, frame_height))
            is_recording = not is_recording
        
        if is_recording:
            out.write(img)
        
        cv2.putText(img, f"SPACE to toggle record: {'' if is_recording else 'not '} recording\n'q' to exit",
            (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.imshow("Image", img)

    source.release()
    out.release()
