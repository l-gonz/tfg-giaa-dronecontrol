import logging
import cv2
import os
import datetime

from dronecontrol.video_source import CameraSource

LOGGING_FORMAT = '%(levelname)s:%(name)s: %(message)s'
IMAGE_FOLDER = 'img'
VIDEO_CODE = cv2.VideoWriter_fourcc('M','J','P','G')


def make_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Return a dedicated logger for a module."""
    log = logging.getLogger(name)
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    log.addHandler(handler)
    return log


def get_formatted_date():
    return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')


def save_image(img, filepath: str=None):
    """Save current captured image to file."""
    if not filepath:
        if not os.path.exists(IMAGE_FOLDER):
            os.makedirs(IMAGE_FOLDER)
        filepath = f"{IMAGE_FOLDER}/{get_formatted_date()}.jpg"
    cv2.imwrite(filepath, img)


def write_video(source):
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    filepath = f"{IMAGE_FOLDER}/{get_formatted_date()}.avi"
    return cv2.VideoWriter(filepath, VIDEO_CODE, 10, source.get_size())


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
    source.close()


def take_video():
    source = CameraSource()
    is_recording = False
    out = None
    
    while True:
        img = source.get_frame()
        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        if key == ord(" "):
            if is_recording:
                out.release()
                out = None
            else:
                out = write_video(source)
            is_recording = not is_recording
        
        if is_recording:
            out.write(img)
        
        cv2.putText(img, f"SPACE to toggle record: {'' if is_recording else 'not '} recording\n'q' to exit",
            (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
        cv2.imshow("Image", img)

    if out:
        out.release()
    source.close()
