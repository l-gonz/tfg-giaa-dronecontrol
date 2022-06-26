import click
from dronecontrol import tools as tools_module
from dronecontrol.follow import start as follow_entry
from dronecontrol.hands import mapper as hands_entry


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    pass

@main.command()
@click.option("-p", "--port", type=int, help="port for UDP connections")
@click.option("--serial", is_flag=False, flag_value="", help="connect to drone system through serial, default device is /dev/ttyUSB0")
@click.option("-f", "--file", type=click.Path(exists=True, readable=True), help="file to use as source instead of the camera")
@click.option("-l", "--log", is_flag=True, help="log important info and save video")
def hand(port, serial, file, log):
    hands_entry.main(port, serial, file, log)

@main.command()
@click.option("--ip", type=str, default="", help="simulator IP address")
@click.option("--sim/--no-sim", "use_simulator", default=True, show_default=True, help="run with AirSim as flight engine")
@click.option("-rs", "--real-sense", "use_realsense", is_flag=True, default=False, show_default=True, help="run with RealSense camera as video source")
@click.option("-l", "--log", is_flag=True, help="log important info and save video")
@click.option("-s", "--serial", is_flag=False, flag_value="", help="use serial to connect to PX4 (HITL), optionally provide the address of the serial port")
def follow(ip, use_simulator, use_realsense, log, serial):
    follow_entry.main(ip, use_simulator, use_realsense, serial, log)

@main.group()
def tools():
    pass

@tools.command()
@click.option("-s", "--sim", "simulator", is_flag=False, flag_value="", help="attach to a simulator through UDP, optionally provide the IP the simulator listens at")
@click.option("-r", "--hardware", is_flag=False, flag_value="", help="attach to a hardware drone through serial, optionally provide the address of the device that connects to PX4")
@click.option("-w", "--wsl", "use_wsl", is_flag=True, help="expects the program to run on a Linux WSL OS")
@click.option("-rs", "--realsense", "use_realsense", is_flag=True, help="use a RealSense camera as source")
@click.option("-h", "--hand-detection", "use_hands", is_flag=True, help="use hand detection for image processing")
@click.option("-p", "--pose-detection", "use_pose", is_flag=True, help="use pose detection for image processing")
def test_camera(simulator, hardware, use_wsl, use_realsense, use_hands, use_pose):
    tools_module.test_camera(simulator is not None, hardware is not None, use_wsl, use_realsense, 
                             use_hands, use_pose, hardware, simulator)

if __name__ == "__main__":
    main()
