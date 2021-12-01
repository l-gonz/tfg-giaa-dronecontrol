import json
from collections import namedtuple

from dronecontrol import graphics, gestures

gui = graphics.HandGui()

def test_no_hand():
    lm = gui.get_landmarks("img/empty.jpg").multi_hand_landmarks
    det = gestures.Detector(lm)
    assert det.get_gesture() == gestures.Gesture.NO_HAND

def test_stop():
    lm = gui.get_landmarks("img/stop.jpg").multi_hand_landmarks
    det = gestures.Detector(lm)
    assert det.get_gesture() == gestures.Gesture.STOP

def test_fist():
    lm = gui.get_landmarks("img/fist.jpg").multi_hand_landmarks
    det = gestures.Detector(lm)
    assert det.get_gesture() == gestures.Gesture.FIST
