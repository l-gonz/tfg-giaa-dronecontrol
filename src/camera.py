import time
import numpy
import logging
import cv2


class handler():
    FONT = cv2.FONT_HERSHEY_PLAIN
    GREEN = (0, 255, 0)
    IMAGE_SCALE = 1.5
    FONT_SCALE = 2
    WIDTH = 640
    HEIGHT = 480


    def __init__(self):
        self.__capture = cv2.VideoCapture(0)
        self.current_time = 0
        self.past_time = 0

        if self.__capture.isOpened():
            self.__capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.WIDTH)
            self.__capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.HEIGHT)
        else:
            logging.error("Can't access camera")


    def is_exit(self):
        return cv2.waitKey(1) >= 0


    def capture(self):
        success, self.img = self.__capture.read()
        if not success:
            self.img = numpy.zeros((self.HEIGHT, self.WIDTH, 3), numpy.uint8)
        return cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB) if success else self.img


    def render(self):
        self.annotate(f"FPS: {self.get_fps()}", 0)
        cv2.imshow("Image", self.img)


    def annotate(self, value, channel=1):
        cv2.putText(self.img, str(value), 
            self.__get_text_pos(channel), 
            self.FONT, self.FONT_SCALE, self.GREEN, self.FONT_SCALE)


    def get_fps(self):
        self.current_time = time.perf_counter()
        fps = 1 / (self.current_time - self.past_time)
        self.past_time = self.current_time
        return int(fps)


    def __get_text_pos(self, channel):
        if channel == 0:
            return (10, 30)
        if channel == 1:
            return (10, self.HEIGHT - 10)
        if channel == 2:
            return (10, self.HEIGHT - 50)


def main():
    cam = handler()
    while True:
        cam.capture()
        cam.annotate("Drone: Take-off", 1)
        cam.annotate("Hand: detected", 2)
        cam.render()
        if cv2.waitKey(1) >= 0:
            break


if __name__ == "__main__":
    main()
