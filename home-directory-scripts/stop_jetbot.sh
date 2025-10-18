#!/bin/bash

# =============================================================================
# JetBot Container Shutdown Wrapper
# =============================================================================
# Convenience script to stop JetBot Docker containers from anywhere
# =============================================================================

# Update this path if your installation is in a different location
JETBOT_DIR="$HOME/source/jetbot-orin"

# Color codes for output
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping JetBot Containers${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if jetbot-orin directory exists
if [ ! -d "$JETBOT_DIR" ]; then
    echo "ERROR: JetBot directory not found at $JETBOT_DIR"
    exit 1
fi

# Change to jetbot-orin directory and run stop script
cd "$JETBOT_DIR"
./stop.sh
