import click
from dronecontrol import tools as tools_module
from dronecontrol.follow import goturn as follow_entry
from dronecontrol.hands import mapper as hands_entry


@click.group()
def main():
    pass

@main.command()
@click.option("-p", "--port", type=int, help="port for UDP connections")
@click.option("--udp", "serial", flag_value=False, default=True, help="connect to drone system through UDP, default address is localhost")
@click.option("--serial", "serial", flag_value=True, help="connect to drone system through serial, default device is ttyUSB0")
# @click.option("-f", "--file", type=click.File, help="file to use as source instead of the camera")
def hand(port, serial):
    hands_entry.main(port, serial)

@main.command()
def follow():
    follow_entry.main()

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
