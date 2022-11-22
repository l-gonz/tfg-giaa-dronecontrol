import traceback
import asyncio
from dronecontrol.tools.test_camera import ImageDetection, VideoCamera
from dronecontrol.tools.test_controller import ControlTest
from dronecontrol.tools.tune_controller import TunePIDController


def test_camera(use_simulator, use_hardware, use_wsl, use_camera, use_hands, use_pose,
                hardware_address=None, simulator_ip=None, file=None):
    detection = ImageDetection.HAND if use_hands else (ImageDetection.POSE if use_pose else ImageDetection.NONE)
    camera = VideoCamera(use_simulator, use_hardware, use_wsl, use_camera, detection, hardware_address, simulator_ip, file)
    try:
        asyncio.run(camera.run())
    except asyncio.CancelledError:
        camera.log.warning("Cancel program run")
    except KeyboardInterrupt:
        camera.log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
    finally:
        camera.close()


def test_controller(is_rotation, data_file):
    control_test = ControlTest(is_rotation, data_file)
    try:
        asyncio.run(control_test.run())
    except asyncio.CancelledError:
        control_test.log.warning("Cancel program run")
    except KeyboardInterrupt:
        control_test.log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
    finally:
        control_test.close()


def tune_pid(tune_yaw, manual, kp_values, ki_values, kd_values):
    control_test = TunePIDController(tune_yaw, manual, kp_values, ki_values, kd_values)
    try:
        asyncio.run(control_test.run())
    except asyncio.CancelledError:
        control_test.log.warning("Cancel program run")
    except KeyboardInterrupt:
        control_test.log.warning("Cancelled with KeyboardInterrupt")
    except:
        traceback.print_exc()
    finally:
        control_test.close()


if __name__ == "__main__":
    test_camera(False, False, False)
