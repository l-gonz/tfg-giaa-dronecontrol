from setuptools import setup

setup(
    name="dronecontrol",
    entry_points={
        'console_scripts': """
            run-file1 = dronecontrol.main:main
        """
    }
)