import cv2
import matplotlib.pyplot as plt

from dronecontrol.common.video_source import FileSource, VideoSourceEmpty
from dronecontrol.common import utils


def drawRectangle(frame, bbox):
    p1 = (int(bbox[0]), int(bbox[1]))
    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
    cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)

def displayRectangle(frame, bbox):
    plt.figure(figsize=(20,10))
    frameCopy = frame.copy()
    drawRectangle(frameCopy, bbox)
    frameCopy = cv2.cvtColor(frameCopy, cv2.COLOR_RGB2BGR)
    plt.imshow(frameCopy); plt.axis('off')    

def drawText(frame, txt, location, color = (50,170,50)):
    cv2.putText(frame, txt, location, cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

def show_start_box(x, y, width, height):
    bbox = (x, y, width, height)
    video = cv2.VideoCapture("img/easy-follow.avi")
    frame = video.read()
    drawRectangle(frame, bbox)
    cv2.imshow("Image", frame)
    while True:
        if cv2.waitKey(10) == 'q':
            break


def main():
    log = utils.make_logger(__name__)
    source = FileSource("img/easy-follow.avi")
    frame = source.get_frame()
    bbox = cv2.selectROI('Select object', frame, False)
    key = cv2.waitKey(500000)
    print(key)
    cv2.destroyWindow('Select object')

    # tracker = cv2.legacy_TrackerBoosting.create()
    # tracker = cv2.TrackerMIL_create()
    # tracker = cv2.TrackerKCF_create()
    # tracker = cv2.legacy_TrackerCSRT.create()
    # tracker = cv2.legacy_TrackerTLD.create()
    # tracker = cv2.legacy_TrackerMedianFlow.create()
    # tracker = cv2.TrackerGOTURN_create()
    tracker = cv2.legacy_TrackerMOSSE.create()

    displayRectangle(frame, bbox)

    ok = tracker.init(frame, bbox)

    while True:
        try:
            frame = source.get_frame()
        except VideoSourceEmpty as e:
            log.warning(e)
            break

        ok, bbox = tracker.update(frame)

        # Draw bounding box
        if ok:
            drawRectangle(frame, bbox)
        else:
            drawText(frame, "Tracking failure detected", (80,140), (0, 0, 255))
            break

        # Display Info
        cv2.imshow("Image", frame)
        cv2.waitKey(50)
        
    source.close()

if __name__ == "__main__":
    main()