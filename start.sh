#!/bin/bash

# =============================================================================
# JetBot Docker Startup Script
# =============================================================================
# This script configures and starts all JetBot Docker containers
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WORKSPACE=${1:-$HOME}
JETBOT_CAMERA=${2:-opencv_gst_camera}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  JetBot Docker Startup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Change to docker directory
cd "$(dirname "$0")/docker"

# Source configuration
echo -e "${GREEN}[1/5]${NC} Loading configuration..."
source configure.sh

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  - JETBOT_VERSION: $JETBOT_VERSION"
echo "  - L4T_VERSION: $L4T_VERSION"
echo "  - JETBOT_BASE_IMAGE: $JETBOT_BASE_IMAGE"
echo "  - JETBOT_I2C_BUS: $JETBOT_I2C_BUS"
echo "  - Workspace: $WORKSPACE"
echo "  - Camera: $JETBOT_CAMERA"
if [[ -n "$JETBOT_JUPYTER_MEMORY" ]]; then
    echo "  - Jupyter Memory: $JETBOT_JUPYTER_MEMORY (Swap: $JETBOT_JUPYTER_MEMORY_SWAP)"
fi
echo ""

# Check if Docker daemon is running
echo -e "${GREEN}[2/5]${NC} Checking Docker status..."
if ! systemctl is-active --quiet docker; then
    echo -e "${YELLOW}Docker is not running. Starting Docker...${NC}"
    sudo systemctl start docker
    sleep 2
fi
echo "  Docker daemon is running"
echo ""

# Stop any existing containers
echo -e "${GREEN}[3/5]${NC} Stopping existing JetBot containers (if any)..."
for container in jetbot_jupyter jetbot_display jetbot_camera; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo "  Stopping and removing: $container"
        docker stop $container 2>/dev/null || true
        docker rm $container 2>/dev/null || true
    fi
done
echo "  Cleanup complete"
echo ""

# Start containers
echo -e "${GREEN}[4/5]${NC} Starting JetBot containers..."

# Start camera container if using ZMQ camera
if [ "$JETBOT_CAMERA" = "zmq_camera" ]; then
    echo "  Starting camera container..."
    ./camera/enable.sh
    sleep 2
fi

# Start display container
echo "  Starting display container..."
./display/enable.sh
sleep 2

# Start Jupyter container
echo "  Starting Jupyter container..."
./jupyter/enable.sh $WORKSPACE $JETBOT_CAMERA
sleep 3

echo ""

# Verify containers are running
echo -e "${GREEN}[5/5]${NC} Verifying container status..."
echo ""

ALL_RUNNING=true
EXPECTED_CONTAINERS="jetbot_jupyter jetbot_display"
if [ "$JETBOT_CAMERA" = "zmq_camera" ]; then
    EXPECTED_CONTAINERS="$EXPECTED_CONTAINERS jetbot_camera"
fi

for container in $EXPECTED_CONTAINERS; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        STATUS=$(docker inspect -f '{{.State.Status}}' $container)
        echo -e "  ${GREEN}✓${NC} $container: $STATUS"
    else
        echo -e "  ${RED}✗${NC} $container: NOT RUNNING"
        ALL_RUNNING=false
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}SUCCESS!${NC} All JetBot containers are running"
    echo ""
    echo -e "${YELLOW}Access Jupyter Lab at:${NC}"
    echo "  https://$(hostname -I | awk '{print $1}'):8888"
    echo "  Password: jetbot"
    echo ""
else
    echo -e "${RED}WARNING:${NC} Some containers failed to start"
    echo "Check logs with: docker logs <container_name>"
    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Container Management Commands:${NC}"
echo ""
echo "  View running containers:"
echo "    docker ps"
echo ""
echo "  View container logs:"
echo "    docker logs -f jetbot_jupyter"
echo "    docker logs -f jetbot_display"
if [ "$JETBOT_CAMERA" = "zmq_camera" ]; then
    echo "    docker logs -f jetbot_camera"
fi
echo ""
echo "  Stop all JetBot containers:"
echo "    docker stop jetbot_jupyter jetbot_display$([ "$JETBOT_CAMERA" = "zmq_camera" ] && echo " jetbot_camera")"
echo ""
echo "  Remove all JetBot containers:"
echo "    docker rm jetbot_jupyter jetbot_display$([ "$JETBOT_CAMERA" = "zmq_camera" ] && echo " jetbot_camera")"
echo ""
echo "  Restart a container:"
echo "    docker restart jetbot_jupyter"
echo ""
echo -e "${RED}To shut down all JetBot services:${NC}"
echo -e "  ${YELLOW}./stop.sh${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
