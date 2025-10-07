# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JetBot is an open-source robot platform based on NVIDIA Jetson Nano. The project combines Python-based robot control software with Jupyter notebooks for interactive AI development. The codebase uses Docker containers for deployment and includes tutorials for collision avoidance, road following, object detection, and teleoperation.

## Build and Installation

### Installing the JetBot Python Package

```bash
python3 setup.py install
```

The setup script automatically runs CMake to build the native TensorRT components before installing the Python package.

### Docker-based Development

The primary deployment method uses Docker containers:

1. **Configure System:**
   ```bash
   ./scripts/configure_jetson.sh
   cd docker
   source configure.sh
   ```

2. **Set NVIDIA Runtime (required for CUDA):**
   ```bash
   ./docker/set_nvidia_runtime.sh
   ```

3. **Build All Containers:**
   ```bash
   cd docker
   ./build.sh
   ```

4. **Enable and Start Services:**
   ```bash
   sudo systemctl enable docker
   ./docker/enable.sh $HOME
   ```

After enabling, access Jupyter Lab at `https://<jetbot_ip>:8888` (password: `jetbot`).

## Documentation

The project uses mkdocs-material for documentation generation.

### Install Documentation Tools

```bash
sudo apt-get update
sudo apt-get -y install python3-pip mkdocs
pip3 install mkdocs-material mike
```

### Preview Documentation Locally

```bash
mkdocs serve --dev-addr=0.0.0.0:8000
```

### Deploy Documentation

```bash
mike deploy <tag>          # Deploy a version
mike set-default master    # Set default version
mike deploy master --push  # Deploy and push to GitHub Pages
```

## Architecture

### Core Python Package Structure

The `jetbot/` package provides the core robot control API:

- **Motor Control (`motor.py`, `robot.py`)**: Dual hardware support via I2C device detection:
  - Adafruit MotorHAT (I2C address 96)
  - SparkFun Qwiic Motor Controller (I2C address 93)
  - The `Robot` class uses `traitlets` for reactive motor control
  - Methods: `forward()`, `backward()`, `left()`, `right()`, `stop()`, `set_motors()`

- **Camera (`camera/`)**: Pluggable camera backends via `JETBOT_DEFAULT_CAMERA` environment variable:
  - `opencv_gst_camera.py`: Default GStreamer-based camera (uses CUDA acceleration)
  - `zmq_camera.py`: ZMQ-based camera for remote video streaming
  - The `Camera` class in `__init__.py` dynamically selects the implementation

- **AI/ML Components**:
  - `tensorrt_model.py`: Generic TensorRT model wrapper with PyTorch tensor bridging
  - `object_detection.py`: SSD-based object detection using TensorRT
  - `ssd_tensorrt/`: Native C++ TensorRT plugins (built via CMake)

- **Utilities**:
  - `heartbeat.py`: LED heartbeat indicator for system status
  - `image.py`: Image conversion utilities (BGR8 to JPEG)
  - `jpeg_encoder.py`: Hardware-accelerated JPEG encoding

### Jupyter Notebooks

Located in `notebooks/`, organized by tutorial:
- `basic_motion/`: Introduction to motor control
- `collision_avoidance/`: Data collection and training for collision avoidance
- `object_following/`: Object detection and following behaviors
- `road_following/`: Lane following with regression models
- `teleoperation/`: Remote control interface

Each tutorial typically has:
- `data_collection.ipynb`: Collect training data
- `train_model.ipynb`: Train neural network (usually PyTorch)
- `live_demo.ipynb`: Run the trained model in real-time

### Docker Architecture

The Docker setup uses a layered approach:
- `base/`: Base image with L4T PyTorch
- `camera/`: Camera service container
- `display/`: Display output container
- `jupyter/`: Main Jupyter Lab container with mounted workspace
- `models/`: Pre-trained model storage

The `configure.sh` script auto-detects L4T version and selects the appropriate base image.

## Hardware Abstraction

The codebase automatically detects motor controller hardware at import time by scanning I2C addresses. When working on motor control:
- Address 96 (0x60): Triggers Adafruit MotorHAT code paths
- Address 93 (0x5D): Triggers SparkFun Qwiic code paths

This detection happens in both `motor.py` and `robot.py` via `qwiic.scan()`.

## Native Builds

The TensorRT SSD detection plugin requires native compilation:
- Root `CMakeLists.txt` configures CUDA and builds `jetbot/ssd_tensorrt`
- The compiled `.so` library is packaged with the Python package
- Build automatically triggered by `setup.py`

## Key Environment Variables

- `JETBOT_DEFAULT_CAMERA`: Set to `zmq_camera` for ZMQ camera backend (default: `opencv_gst_camera`)
- `JETBOT_BASE_IMAGE`: Docker base image (auto-detected from L4T version)
- `JETBOT_JUPYTER_MEMORY`: Jupyter container memory limit
- `JETBOT_JUPYTER_MEMORY_SWAP`: Jupyter container swap limit

## Notes

- The project targets NVIDIA Jetson Nano with L4T (Linux for Tegra)
- Motor directions may need inversion depending on physical wiring
- The Waveshare JetBot board requires special PWM handling (see motor.py lines 80-87, 92-94)
- Jupyter workspace is mounted from host, so work in `/workspace` persists across container restarts
