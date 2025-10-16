#!/bin/bash

# =============================================================================
# JetBot Docker Shutdown Script
# =============================================================================
# This script stops and removes all JetBot Docker containers
# =============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  JetBot Docker Shutdown Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# List of all possible JetBot containers
CONTAINERS="jetbot_jupyter jetbot_display jetbot_camera"

echo -e "${YELLOW}Stopping JetBot containers...${NC}"
echo ""

STOPPED_COUNT=0
for container in $CONTAINERS; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -n "  Stopping $container... "
        if docker stop $container >/dev/null 2>&1; then
            echo -e "${GREEN}done${NC}"
            ((STOPPED_COUNT++))
        else
            echo -e "${RED}failed${NC}"
        fi

        echo -n "  Removing $container... "
        if docker rm $container >/dev/null 2>&1; then
            echo -e "${GREEN}done${NC}"
        else
            echo -e "${RED}failed${NC}"
        fi
    else
        echo -e "  $container: ${YELLOW}not found${NC}"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"

if [ $STOPPED_COUNT -gt 0 ]; then
    echo -e "${GREEN}Shutdown complete!${NC} Stopped $STOPPED_COUNT container(s)"
else
    echo -e "${YELLOW}No running JetBot containers found${NC}"
fi

echo ""
echo "To start JetBot again, run:"
echo -e "  ${GREEN}./start.sh${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
