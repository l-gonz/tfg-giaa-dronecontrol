import time
import cv2


class handler():
    FONT = cv2.FONT_HERSHEY_PLAIN
    GREEN = (255, 0, 255)

    def __init__(self):
        self.__capture = cv2.VideoCapture(0)
        self.current_time = 0
        self.past_time = 0

    def is_exit(self):
        return cv2.waitKey(1) >= 0

    def capture(self):
        success, self.img = self.__capture.read()
        if success:
            imgRGB = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
            return imgRGB
        return None

    def render(self):
        fps = self.get_fps()
        cv2.putText(self.img, str(fps), (10, 70), self.FONT, 3, self.GREEN, 3)
        cv2.imshow("Image", self.img)

    def annotate(self, value):
        print(value)

    def get_fps(self):
        self.current_time = time.perf_counter()
        fps = 1 / (self.current_time - self.past_time)
        self.past_time = self.current_time
        return int(fps)
