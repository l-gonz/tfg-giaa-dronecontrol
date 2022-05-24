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
@click.option("--udp", "serial", flag_value=False, default=True, help="connect to drone system through UDP, default address is localhost")
@click.option("--serial", "serial", flag_value=True, help="connect to drone system through serial, default device is ttyUSB0")
@click.option("-f", "--file", type=click.Path(exists=True, readable=True), help="file to use as source instead of the camera")
@click.option("-l", "--log", is_flag=True, help="log important info and save video")
def hand(port, serial, file, log):
    print(f"Port: {port}, serial: {serial}, file: {file}")
    hands_entry.main(port, serial, file, log)

@main.command()
@click.option("--ip", type=str, default="", help="simulator IP address")
@click.option("--sim/--no-sim", "use_simulator", default=True, help="run with AirSim as video source (default True)")
@click.option("-l", "--log", is_flag=True, help="log important info and save video")
def follow(ip, use_simulator, log):
    follow_entry.main(ip, use_simulator, log)

@main.group()
def tools():
    pass

@tools.command()
@click.option("-s", "--sim", "use_simulator", is_flag=True, help="attach to a simulator through UDP")
@click.option("-h", "--hardware", "use_hardware", is_flag=True, help="attach to a hardware drone through serial")
@click.option("-w", "--wsl", "use_wsl", is_flag=True, help="attach to a hardware drone through serial")
# @click.option("--address", help="address to attach to, default for UDP is localhost and for serial ttyUSB0")
def test_camera(use_simulator, use_hardware, use_wsl):
    tools_module.test_camera(use_simulator, use_hardware, use_wsl)

if __name__ == "__main__":
    main()
