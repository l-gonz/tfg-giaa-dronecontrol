import os
import logging
import typing
import cv2
import numpy
import time
import matplotlib.pyplot as plt
from datetime import datetime
from enum import Enum
from mediapipe.python.solution_base import SolutionBase

from dronecontrol.tools import tools
from dronecontrol.common import pilot


LOGGING_FORMAT = '%(levelname)s:%(name)s: %(message)s'
SYSTEM_INFO_FORMATTER = '%(asctime)s,%(message)s'
IMAGE_FOLDER = 'img'
VIDEO_CODE = cv2.VideoWriter_fourcc('M','J','P','G')


FONT = cv2.FONT_HERSHEY_PLAIN
FONT_SCALE = 1


class Color():
    """Define color constants to use with cv2."""
    GREEN = (0, 255, 0)
    PINK = (255, 0, 255)
    BLUE = (255, 0, 0)
    RED = (0, 0, 255)

class ImageLocation(Enum):
    TOP_LEFT = 0
    BOTTOM_LEFT = 1
    BOTTOM_LEFT_LINE_TWO = 2


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
    """Close the handlers on a file logger."""
    if logger is None:
        return

    handlers = logger.handlers[:]
    for handler in handlers:
        logger.removeHandler(handler)
        handler.close()


async def log_system_info(log: logging.Logger, pilot: pilot.System, tracking_info: str):
    """Log useful information about a pilot system to a dedicated logger."""
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


def write_text_to_image(image, text, location=ImageLocation.BOTTOM_LEFT):
    """Annotate an image with the given text.
        
    Several locations available for positioning the text."""
    cv2.putText(image, str(text), __get_text_pos(image, location),
        FONT, FONT_SCALE, Color.BLUE, FONT_SCALE)


def __get_text_pos(image, location: ImageLocation) -> typing.Tuple[int,int]:
    """Map image location enum to pixel position."""
    if location == ImageLocation.TOP_LEFT:
        return (10, 30)
    if location == ImageLocation.BOTTOM_LEFT:
        return (10, image.shape[0] - 10)
    if location == ImageLocation.BOTTOM_LEFT_LINE_TWO:
        return (10, image.shape[0] - 30)


def get_wsl_host_ip():
    """
    In a Linux system, returns the IP of the host Windows 
    computer on the internal virtual network.
    """
    ip = ""
    if not os.path.exists("/etc/resolv.conf"):
        return ip

    with open("/etc/resolv.conf") as file:
        for line in file:
            if "nameserver" in line:
                ip = line.split()[-1]
                break
    return ip


def plot(x, y, subplots=None, block=True, title="TEST PID", xlabel="time (s)", ylabel="PID (PV)", legend=None):
    """Helper function to plot data with different styles."""
    if len(x) == 0:
        return
    
    x = numpy.array(x, dtype=object)
    y = numpy.array(y, dtype=object)
    plt.figure()
    plt.xlabel(xlabel)
    plt.grid(True)
    plt.title(title)

    if subplots:
        count = 0
        for i, subplot in enumerate(subplots):
            plt.subplot(len(subplots), 1, i+1)
            plt.plot(x[:], numpy.transpose(y[count:count+subplot]))
            plt.grid(True)
            plt.ylabel(ylabel[i])
            count += subplot
    else:
        if x.shape[0] != y.shape[0]:
            for y_data in y:
                plt.plot(x, y_data)
        elif x.shape == y.shape:
            for i in range(x.shape[0]):
                plt.plot(x[i], y[i])
        else:
            raise Exception("Unmatched data")
        plt.ylabel(ylabel)

    if legend:
        plt.legend(legend)
    plt.show(block=block)


async def measure(func, time_list: list, is_async: bool, *args):
    """Execute a function and measure the time that it takes to run.
    
    Adds the time to the end of the list of values provided in time_list."""
    start_time = time.perf_counter()
    if is_async:
        result = await func(*args)
    else:
        result = func(*args)
    end_time = time.perf_counter()
    time_list.append(end_time - start_time)
    return result


def write_image(img, filepath: str=None):
    """Save image to file."""
    if not filepath:
        if not os.path.exists(IMAGE_FOLDER):
            os.makedirs(IMAGE_FOLDER)
        filepath = f"{IMAGE_FOLDER}/{get_formatted_date()}.jpg"
    cv2.imwrite(filepath, img)


def write_video(size):
    """Save video to file."""
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)
    filepath = f"{IMAGE_FOLDER}/{get_formatted_date()}.avi"
    return cv2.VideoWriter(filepath, VIDEO_CODE, 30, size)


def get_formatted_date():
    """Get current date as a formatted string for a file name."""
    return datetime.now().strftime('%Y%m%d-%H%M%S')
