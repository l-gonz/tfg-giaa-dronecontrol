import asyncio
from dronecontrol import mapper


def main():
    asyncio.run(mapper.run())


if __name__ == "__main__":
    main()
