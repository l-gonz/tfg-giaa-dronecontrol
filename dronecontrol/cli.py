import click
from dronecontrol import tools as tools_module
from dronecontrol.follow import start as follow_entry
from dronecontrol.hands import mapper as hands_entry


@click.group()
def main():
    pass

@main.command()
@click.option("-p", "--port", type=int, help="port for UDP connections")
@click.option("--udp", "serial", flag_value=False, default=True, help="connect to drone system through UDP, default address is localhost")
@click.option("--serial", "serial", flag_value=True, help="connect to drone system through serial, default device is ttyUSB0")
@click.option("-f", "--file", type=click.Path(exists=True, readable=True), help="file to use as source instead of the camera")
def hand(port, serial, file):
    print(f"Port: {port}, serial: {serial}, file: {file}")
    hands_entry.main(port, serial, file)

@main.command()
@click.option("--ip", type=str, default=None, help="simulator IP address")
@click.option("--sim/--no-sim", "use_simulator", default=True, help="run with AirSim as video source (default True)")
def follow(ip, use_simulator):
    follow_entry.main(ip, use_simulator)

@main.group()
def tools():
    pass

@tools.command()
def take_image():
    tools_module.take_images()

@tools.command()
def take_video():
    tools_module.take_video()

if __name__ == "__main__":
    main()
