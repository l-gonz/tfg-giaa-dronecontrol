Tested on Ubuntu 20.04 inside WSL

# Installation

Execute the installation file after cloning the repository:
```shell
bash ./install.sh
```

The script installs the PX4 dependencies, creates a virtual environment for the project and installs the dronevisioncontrol package in edit mode.

# Run in simulator

1. Start simulator: `./simulator.sh`
2. Run app: `python -m dronevisioncontrol`
