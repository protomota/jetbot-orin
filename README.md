# JetBot

<img src="https://jetbot.org/master/images/jetbot_800x630.png" height="256">

JetBot is an open-source robot based on NVIDIA Jetson Nano that is

* **Affordable** - Less than $150 add-on to Jetson Nano
* **Educational** - Tutorials from basic motion to AI based collision avoidance
* **Fun!** - Interactively programmed from your web browser

Building and using JetBot gives the hands on experience needed to create entirely new AI projects.

> Looking for a quick way to get started with JetBot? Many third party kits are [now available](https://jetbot.org/master/third_party_kits.html)!

## Getting Started

### Step 0 - Hardware Setup and Motor Controller Configuration

Before running the software, ensure your hardware is properly configured:

#### Motor Controller Power

The Adafruit MotorHAT/FeatherWing motor controller requires **external power** (6-12V) separate from the Jetson.

**Important**: Check that the motor controller has a **green power LED lit at all times**. Some power banks automatically shut down if they detect low current draw, thinking nothing is connected. If you're using a power bank:
- Use a power bank that supports low-current devices
- OR use a dedicated battery pack designed for robotics
- Monitor the green LED - if it turns off, your power source has shut down

#### I2C Bus Configuration

The motor controller may be on a non-default I2C bus. To check which bus your motor controller is on:

```bash
# Check all I2C buses for the motor controller
for bus in 0 1 2 7; do
  echo "=== Bus $bus ==="
  i2cdetect -y -r $bus
done
```

Look for:
- Address `60` (0x60) - Adafruit MotorHAT
- Address `5d` (0x5D) - SparkFun Qwiic Motor Controller

If your motor controller is **not on bus 1** (the default), you need to set the `JETBOT_I2C_BUS` environment variable:

```bash
# Add to ~/.bashrc for persistence
echo 'export JETBOT_I2C_BUS=7' >> ~/.bashrc
source ~/.bashrc
```

Replace `7` with whichever bus number shows your motor controller.

#### Installing the JetBot Python Package

```bash
cd ~/source/jetbot-source
python3 setup.py install --user
```

#### Testing Your Motors

Test that motors are working:

```bash
python3 ~/source/jetbot-source/test_motors_simple.py
```

If motors don't move:
1. Check the green power LED on the motor controller
2. Verify external power supply is connected and ON
3. Check motor connections to M1/M2 terminals
4. Ensure `JETBOT_I2C_BUS` is set correctly (if not using bus 1)

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

### Power Mode (Jetson Orin Nano 8GB)

For **Jetson Orin Nano 8GB Developer Kit**, we recommend lowering the power mode to 3W for optimal battery operation:

```bash
sudo nvpmodel -m 3
```

Then verify it worked:

```bash
sudo nvpmodel -q
```

This prevents shutdowns during high motor loads and extends battery life.

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
cd docker
./disable.sh
```

### Rebuild Containers

```bash
cd docker
./disable.sh
./build.sh
./enable.sh $HOME
```

## Important Notes

- The containers will restart automatically on boot
- Work saved outside of `/workspace` in the Jupyter container will be lost when the container restarts
- The NVIDIA runtime is automatically configured by `configure.sh`
- Docker daemon is automatically enabled at boot by `configure.sh`

## Documentation

For more detailed information and tutorials, read the [JetBot documentation](https://jetbot.org).

## Get Involved

We really appreciate any feedback related to JetBot, and also just enjoy seeing what you're working on! There is a growing community of Jetson Nano and JetBot users. It's easy to get involved...

* Ask a question and discuss JetBot related topics on the [JetBot GitHub Discussions](https://github.com/NVIDIA-AI-IOT/jetbot/discussions)
* Report a bug by [creating an issue](https://github.com/NVIDIA-AI-IOT/jetbot/issues)
* Share your project or ask a question on the [Jetson Developer Forums](https://devtalk.nvidia.com/default/board/139/jetson-embedded-systems/)
