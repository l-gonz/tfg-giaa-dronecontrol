import click
from dronecontrol.hands import mapper, graphics
from dronecontrol.follow import start


@click.group()
def main():
    pass

@main.command()
@click.option("-p", "--port", type=int, help="port for UDP connections")
@click.option("--udp", "serial", flag_value=False, default=True, help="connect to drone system through UDP, default address is localhost")
@click.option("--serial", "serial", flag_value=True, help="connect to drone system through serial, default device is ttyUSB0")
def hand(port, serial):
    mapper.main(port, serial)

@main.command()
def follow():
    start.main()

@main.group()
def utils():
    pass

@utils.command()
def take_image():
    graphics.take_images()

@utils.command()
def take_video():
    graphics.take_video()
