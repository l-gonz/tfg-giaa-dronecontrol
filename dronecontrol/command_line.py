import click

from dronecontrol import mapper
from dronecontrol import graphics

@click.group()
def main():
    pass

@click.command()
def hand():
    mapper.main()

@click.command()
def take_image():
    graphics.take_images()

main.add_command(hand)
main.add_command(take_image)