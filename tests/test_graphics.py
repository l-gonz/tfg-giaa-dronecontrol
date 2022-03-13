import pytest
import numpy
from dronecontrol.hands import graphics
from dronecontrol.hands import gestures

NO_CAM = 999

def test_loop():
    gui = graphics.HandGui()
    gui.capture()
    assert gui.render() == -1

def test_render_no_capture():
    gui = graphics.HandGui()
    assert gui.render() == -1

def test_annotate_fps():
    gui = graphics.HandGui(NO_CAM)
    gui.capture()
    gui.render(True, False)
    assert numpy.any(gui.img)

def test_hands_no_cam():
    gui = graphics.HandGui(NO_CAM)
    gui.capture()
    gui.render(False, True)
    assert not numpy.any(gui.img)

def test_render_no_cam():
    gui = graphics.HandGui(NO_CAM)
    gui.capture()
    gui.render(False, False)
    assert not numpy.any(gui.img)

def test_subscriptions():
    gui = graphics.HandGui(NO_CAM)
    def check_no_hand(g):
        assert g is gestures.Gesture.NO_HAND
        raise SystemExit
    gui.subscribe_to_gesture(check_no_hand)

    with pytest.raises(SystemExit):
        gui.capture()

def test_clear_subscriptions():
    gui = graphics.HandGui(NO_CAM)
    def check_not_called(g):
        assert False

    gui.subscribe_to_gesture(check_not_called)
    gui.unsubscribe_to_gesture(check_not_called)
    gui.capture()
    assert True
