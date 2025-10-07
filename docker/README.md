# JetBot Docker

This directory contains scripts to build and run the JetBot docker containers.

For setup instructions, see the main [README.md](../README.md) in the root of this repository.

## Directory Structure

- `base/` - Base Docker image configuration
- `camera/` - Camera service container
- `display/` - Display output container
- `jupyter/` - Jupyter Lab container (main interface)
- `models/` - Pre-trained model storage

## Scripts

- `configure.sh` - Detects L4T version and sets environment variables
- `build.sh` - Builds all Docker containers
- `enable.sh` - Starts and enables containers to run at boot
- `disable.sh` - Stops all JetBot containers
- `set_nvidia_runtime.sh` - Configures Docker to use NVIDIA runtime (called by configure.sh)
