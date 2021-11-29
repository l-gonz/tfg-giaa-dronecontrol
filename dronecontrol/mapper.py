from gestures import Gesture
from pilot import System

def map_gesture_to_action(gesture) -> tuple[function, dict]:
    """Map a hand gesture to a drone action.
    
    Returns an action function and a parameter dictionary."""
    
    if gesture == Gesture.NO_HAND:
        return System.return_home, {}
    if gesture == Gesture.STOP:
        return System.land, {}
    if gesture == Gesture.FIST:
        return System.takeoff, {}