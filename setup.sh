#!/bin/bash
PX4="PX4-Autopilot"

# Install conda
wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.10.3-Linux-x86_64.sh
bash Miniconda3-py39_4.10.3-Linux-x86_64.sh
conda update conda
conda env create -p conda-env -f environment.yml
conda activate ./conda-env

sudo apt-get update && \
    apt-get install -y git && \
    apt-get -y autoremove && \
    apt-get clean autoclean && \
    rm -rf /var/lib/apt/lists/{apt,dpkg,cache,log} /tmp/* /var/tmp/*

mkdir Firmware
cd Firmware

# PX4
if [[ ! -d $PX4 ]]
then
    git clone https://github.com/PX4/PX4-Autopilot.git
fi
git -C $PX4 checkout master
git -C $PX4 submodule update --init --recursive

./$PX4/Tools/setup/ubuntu.sh

# QGroundControl
sudo usermod -a -G dialout $USER
sudo apt-get remove modemmanager -y
sudo apt install gstreamer1.0-plugins-bad gstreamer1.0-libav gstreamer1.0-gl -y

wget "https://s3-us-west-2.amazonaws.com/qgroundcontrol/builds/master/QGroundControl.AppImage"
chmod u+x ./QGroundControl.AppImage

# Build
cd $PX4
DONT_RUN=1 make px4_sitl jmavsim

# conda installs this
# sudo pip3 install mavsdk aioconsole
# conda install -c conda-forge opencv
