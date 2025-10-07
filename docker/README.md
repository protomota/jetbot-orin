# JetBot Docker

This directory contains scripts to build and run the JetBot docker containers.

## Quick Start

### Step 1 - Configure System

First, call the `scripts/configure_jetson.sh` script to configure the power mode and other parameters.

```bash
cd jetbot
./scripts/configure_jetson.sh
```

### Step 2 - Configure Docker Environment

Navigate to the docker directory and source the `configure.sh` script to configure environment variables.

```bash
cd docker
source configure.sh
```

The script will automatically detect your L4T version and set the appropriate base image. If your L4T version is not recognized, you may see a warning. In that case, manually set the base image:

```bash
export JETBOT_BASE_IMAGE=<appropriate-base-image>
```

Refer to https://ngc.nvidia.com/catalog/containers/nvidia:l4t-pytorch for available base images.

### Step 3 - Build Docker Containers

Build all JetBot containers from scratch:

```bash
./build.sh
```

This step is required before running the containers for the first time.

### Step 4 - Enable and Start Containers

Enable Docker to start at boot and launch the JetBot containers:

```bash
./enable.sh $HOME
```

The directory you specify (e.g., `$HOME`) will be mounted as `/workspace` in the Jupyter container. All work saved in `/workspace` will persist across container restarts.

### Step 5 - Access Jupyter Lab

Open your web browser and navigate to:

```
https://<jetbot_ip>:8888
```

The default password is `jetbot`.

![](https://user-images.githubusercontent.com/25759564/92091965-51ae4f00-ed86-11ea-93d5-09d291ccfa95.png)

## Optional Configuration

### Memory Limits

If you need to set memory limits on the Jupyter container (automatically configured for systems with less than 3GB RAM):

```bash
export JETBOT_JUPYTER_MEMORY=500m
export JETBOT_JUPYTER_MEMORY_SWAP=3G
```

Set these environment variables before running `./enable.sh`.

## Managing Containers

### Stop All Containers

```bash
./disable.sh
```

### Rebuild Containers

```bash
./disable.sh
./build.sh
./enable.sh $HOME
```

## Important Notes

- The containers will restart automatically on boot
- Work saved outside of `/workspace` in the Jupyter container will be lost when the container restarts
- The NVIDIA runtime is automatically configured by `configure.sh`
- Docker daemon is automatically enabled at boot by `configure.sh`
