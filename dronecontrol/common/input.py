"""
Utility module to map keyboard inputs to pilot or tool actions

@author: Laura Gonzalez
"""

from mediapipe.python.solution_base import SolutionBase
from dronecontrol.common import utils, pilot
from dronecontrol.tools import tools

class InputHandler:
    """Handles a key input and converts it to a function."""
    def __init__(self):
        self.log = utils.make_stdout_logger(__name__)

    def handle(self, key: int):
        if key < 0:
            return None

        self.log.info(f"Pressed [{chr(key)}]")
        if key == ord('z'): # Quit
            raise KeyboardInterrupt
        elif key == ord('k'): # Kill switch
            return pilot.System.kill_engines
        elif key == ord('h'): # Return home
            return pilot.System.return_home
        elif key == ord('0'): # Stop
            return pilot.System.set_velocity
        elif key == ord('t'): # Take-off
            return pilot.System.takeoff
        elif key == ord('l'): # Land
            return pilot.System.land
        elif key == ord('o'): # Toggle offboard
            return pilot.System.toggle_offboard
        elif key == ord('w'): # Forward
            return pilot.System.move_fwd_positive
        elif key == ord('s'): # Backward
            return pilot.System.move_fwd_negative
        elif key == ord('d'): # Right
            return pilot.System.move_right
        elif key == ord('a'): # Left
            return pilot.System.move_left
        elif key == ord('q'): # Yaw left
            return pilot.System.move_yaw_left
        elif key == ord('e'): # Yaw right
            return pilot.System.move_yaw_right
        elif key == ord('1'): # Up
            return pilot.System.move_up
        elif key == ord('3'): # Down
            return pilot.System.move_down
        elif key == ord(' '): # Take picture / start video
            return tools.VideoCamera.trigger
        elif key == ord('<'): # Picture <> video
            return tools.VideoCamera.change_mode
        elif key == ord('r'): # Reset image processing
            return SolutionBase.process

        else:
            log.warning(f"Key {chr(key)}:{key} is not bound to any action.")