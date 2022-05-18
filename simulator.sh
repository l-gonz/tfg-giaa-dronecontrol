#!/bin/bash

cd Firmware/PX4-Autopilot

if [ "$1" == "--airsim" ]
then
    echo "Starting PX4 for AirSim"
    export PX4_SIM_HOST_ADDR=$(cat /etc/resolv.conf | grep "nameserver " | awk '{print $2}')
    make px4_sitl none_iris
elif [ "$1" == "--gazebo" ]
then
    make px4_sitl gazebo
elif [ "$1" == "--headless" ]
then
    HEADLESS=1 make px4_sitl gazebo
else
    echo "Provide simulator option"
fi
