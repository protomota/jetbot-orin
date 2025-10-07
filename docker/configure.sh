#!/bin/bash

export JETBOT_VERSION=0.4.3

L4T_VERSION_STRING=$(head -n 1 /etc/nv_tegra_release)
L4T_RELEASE=$(echo $L4T_VERSION_STRING | cut -f 2 -d ' ' | grep -Po '(?<=R)[^;]+')
L4T_REVISION=$(echo $L4T_VERSION_STRING | cut -f 2 -d ',' | grep -Po '(?<=REVISION: )[^;]+')


export L4T_VERSION="$L4T_RELEASE.$L4T_REVISION"

if [[ "$L4T_VERSION" == "36.4.7" ]] || [[ "$L4T_VERSION" == "36.4.4" ]] || [[ "$L4T_VERSION" == "36.4.3" ]] || [[ "$L4T_VERSION" == "36.4.0" ]]
then
	JETBOT_BASE_IMAGE=dustynv/l4t-pytorch:r36.4.0
elif [[ $L4T_VERSION = "32.4.3" ]]
then
	JETBOT_BASE_IMAGE=nvcr.io/nvidia/l4t-pytorch:r32.4.3-pth1.6-py3
elif [[ "$L4T_VERSION" == "32.4.4" ]]
then
	JETBOT_BASE_IMAGE=nvcr.io/nvidia/l4t-pytorch:r32.4.4-pth1.6-py3
elif [[ "$L4T_VERSION" == "32.5.0" ]] || [[ "$L4T_VERSION" == "32.5.1" ]]
then
	JETBOT_BASE_IMAGE=nvcr.io/nvidia/l4t-pytorch:r32.5.0-pth1.6-py3
else
	echo "JETBOT_BASE_IMAGE not found for ${L4T_VERSION}.  Please manually set the JETBOT_BASE_IMAGE environment variable. (ie: export JETBOT_BASE_IMAGE=...)"
fi

export JETBOT_BASE_IMAGE
export JETBOT_DOCKER_REMOTE=jetbot

echo "JETBOT_VERSION=$JETBOT_VERSION"
echo "L4T_VERSION=$L4T_VERSION"
echo "JETBOT_BASE_IMAGE=$JETBOT_BASE_IMAGE"

./set_nvidia_runtime.sh
sudo systemctl enable docker

# check system memory
SYSTEM_RAM_KILOBYTES=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)

if [ $SYSTEM_RAM_KILOBYTES -lt 3000000 ]
then
    export JETBOT_JUPYTER_MEMORY=500m
    export JETBOT_JUPYTER_MEMORY_SWAP=3G
fi

# Auto-detect I2C bus for motor controller and OLED display
# Scan common I2C buses for Adafruit MotorHAT (0x60) AND OLED (0x3c)
# Prioritize buses with both devices
JETBOT_I2C_BUS=1  # default
for bus in 7 1; do
    BUS_SCAN=$(i2cdetect -y -r $bus 2>/dev/null)
    HAS_MOTOR=$(echo "$BUS_SCAN" | grep -c "60")
    HAS_OLED=$(echo "$BUS_SCAN" | grep -c "3c")

    # If both motor and OLED found, use this bus (best match)
    if [ "$HAS_MOTOR" -gt 0 ] && [ "$HAS_OLED" -gt 0 ]; then
        JETBOT_I2C_BUS=$bus
        echo "JETBOT_I2C_BUS=$JETBOT_I2C_BUS (motor+OLED detected)"
        break
    # If only motor found, use this bus but keep looking
    elif [ "$HAS_MOTOR" -gt 0 ]; then
        JETBOT_I2C_BUS=$bus
        echo "JETBOT_I2C_BUS=$JETBOT_I2C_BUS (motor detected)"
    fi
done

export JETBOT_I2C_BUS

