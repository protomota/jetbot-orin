#!/bin/bash

# Disable GUI to free up more RAM
sudo systemctl set-default multi-user

# Disable ZRAM
sudo systemctl disable nvzramconfig.service

# Default to 3W power mode (battery-friendly)
sudo nvpmodel -m 3

