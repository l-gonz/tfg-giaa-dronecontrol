import os
import logging
import typing
import cv2
from datetime import datetime
from mediapipe.python.solution_base import SolutionBase

from dronecontrol import tools
from dronecontrol.common import pilot


LOGGING_FORMAT = '%(levelname)s:%(name)s: %(message)s'
SYSTEM_INFO_FORMATTER = '%(asctime)s,%(message)s'


FONT = cv2.FONT_HERSHEY_PLAIN
FONT_SCALE = 1


class Color():
    """Define color constants to use with cv2."""
    GREEN = (0, 255, 0)
    PINK = (255, 0, 255)
    BLUE = (255, 0, 0)
    RED = (0, 0, 255)


def make_stdout_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Return a dedicated logger for a module."""
    log = logging.getLogger(name)
    log.setLevel(level)
    log.propagate = False

    if len(log.handlers) == 0:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
        log.addHandler(handler)
    return log


def make_file_logger(name: str, level=logging.INFO, for_system_info=True) -> logging.Logger:
    """Return a logger that outputs to a file"""
    log = logging.getLogger(name + "_file")
    log.setLevel(level)
    log.propagate = False

    if len(log.handlers) == 0:
        handler = logging.FileHandler(f"log_{name}_{datetime.now():%d%m%y%H%M%S}")
        handler.setFormatter(logging.Formatter(SYSTEM_INFO_FORMATTER if for_system_info else LOGGING_FORMAT))
        log.addHandler(handler)

        if for_system_info:
            with open(handler.baseFilename, 'w') as file:
                file.write("date,landed_state,flight_mode,position,attitude,velocity,image_info")
    return log


def close_file_logger(logger: logging.Logger):
    if logger is None:
        return

    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()


async def log_system_info(log: logging.Logger, pilot: pilot.System, tracking_info: str):
    if log is None:
        return

    if not pilot.is_ready:
        log.info('%s,%s,%s,%s,%s,%s', "N/A", "N/A", "N/A", "N/A", "N/A", str(tracking_info))
        return

    landed_state = str(await pilot.get_landed_state())
    flight_mode = str(await pilot.get_flight_mode())
    position = str(await pilot.get_position())
    attitude = str(await pilot.get_attitude())
    velocity = str(await pilot.get_velocity())

    log.info('%s,%s,%s,%s,%s,%s', landed_state, flight_mode, position, attitude, velocity, tracking_info)


def write_text_to_image(image, text, channel=1):
    """Annotate an image with the given text.
        
    Several channels available for positioning the text."""
    cv2.putText(image, str(text), __get_text_pos(image, channel),
        FONT, FONT_SCALE, Color.GREEN, FONT_SCALE)


def __get_text_pos(image, channel) -> typing.Tuple[int,int]:
    """Map channel number to pixel position."""
    if channel == 0:
        return (10, 30)
    if channel == 1:
        return (10, image.shape[0] - 10)
    if channel == 2:
        return (10, image.shape[0] - 50)


def get_wsl_host_ip():
    ip = ""
    if not os.path.exists("/etc/resolv.conf"):
        return ip

    with open("/etc/resolv.conf") as file:
        for line in file:
            if "nameserver" in line:
                ip = line.split()[-1]
                break
    return ip


def keyboard_control(key: int):
    if key < 0:
        return None

    log = make_stdout_logger(__name__)

    log.info(f"Pressed [{chr(key)}]")
    if key == ord('q'): # Quit
        raise KeyboardInterrupt
    elif key == ord('k'): # Kill switch
        return pilot.System.kill_engines
    elif key == ord('h'): # Return home
        return pilot.System.return_home
    elif key == ord('s'): # Stop
        return pilot.System.set_velocity
    elif key == ord('t'): # Take-off
        return pilot.System.takeoff
    elif key == ord('l'): # Land
        return pilot.System.land
    elif key == ord('o'): # Toggle offboard
        return pilot.System.toggle_offboard
    elif key == ord(' '): # Take picture / start video
        return tools.VideoCamera.trigger
    elif key == ord('<'): # Picture <> video
        return tools.VideoCamera.change_mode
    elif key == ord('r'): # Reset image processing
        return SolutionBase.process

    else:
        log.warning(f"Key {chr(key)} is not bound to any action.")
