# Home Directory Wrapper Scripts for JetBot

These scripts are designed to be copied to your home directory (`~/`) for convenient access to JetBot Docker containers from anywhere.

## Installation

1. **Update the path in each script** (if your installation is not at `~/source/jetbot-orin`):

```bash
# Edit each script and update the JETBOT_DIR path
nano home-directory-scripts/start_jetbot.sh
nano home-directory-scripts/stop_jetbot.sh
```

2. **Copy scripts to your home directory**:

```bash
cp home-directory-scripts/* ~/
chmod +x ~/start_jetbot.sh ~/stop_jetbot.sh
```

## Scripts

### `start_jetbot.sh`
**Purpose**: Start JetBot Docker containers from anywhere
**Location**: Copy to `~/start_jetbot.sh`

**Usage**:
```bash
# Start with default workspace (workspace_host)
~/start_jetbot.sh

# Start with specific workspace
~/start_jetbot.sh workspace_collision

# Start with specific workspace and camera type
~/start_jetbot.sh workspace_collision csi
```

**What it does**:
- Changes to the jetbot-orin directory
- Runs `./start.sh` with any provided arguments
- Starts JetBot Docker containers (jetbot_jupyter and jetbot_display)
- Returns to original directory when done

**Arguments** (optional):
1. `workspace` - Which workspace to use (default: workspace_host)
   - workspace_host
   - workspace_collision
   - workspace_road_following
   - workspace_object_following
2. `camera_type` - Camera type (default: csi)
   - csi - CSI camera
   - usb - USB camera

---

### `stop_jetbot.sh`
**Purpose**: Stop JetBot Docker containers from anywhere
**Location**: Copy to `~/stop_jetbot.sh`

**Usage**:
```bash
~/stop_jetbot.sh
```

**What it does**:
1. Changes to the jetbot-orin directory
2. Runs `./stop.sh` to stop all JetBot containers
3. Stops jetbot_jupyter and jetbot_display Docker containers
4. Preserves Jupyter notebooks and workspaces

---

## Why These Scripts?

These wrapper scripts allow you to:
- Start/stop JetBot containers from any directory
- Avoid having to `cd` to the jetbot-orin folder
- Have quick access to common operations
- Maintain consistent paths regardless of where you are in the filesystem

## JetBot Container System

The jetbot-orin project uses Docker containers to provide:
- **jetbot_jupyter**: Jupyter Lab environment for notebooks
- **jetbot_display**: Display server for visualization

These containers provide the standard NVIDIA JetBot environment with:
- Jupyter notebooks for training (collision avoidance, road following, object following)
- Pre-installed JetBot Python library
- Camera support (CSI or USB)
- Motor control support

## Relationship with JetBot Rover

The jetbot-orin project provides:
- ✅ Training notebooks for collision avoidance models
- ✅ Training notebooks for road following models
- ✅ Training notebooks for object following models
- ✅ Jupyter Lab environment for data collection
- ✅ Standard NVIDIA JetBot library

The jetbot-rover project uses trained models from jetbot-orin:
- Uses collision avoidance models trained in jetbot-orin
- Will use road following models (future)
- Will use object following models (future)
- Provides production inference and navigation

**Workflow**:
1. Use jetbot-orin to collect data and train models
2. Copy trained models to jetbot-rover/models/
3. Use jetbot-rover for production navigation

## Notes

- All scripts assume the jetbot-orin directory is at `~/source/jetbot-orin`
- **If your installation is in a different location**, edit the `JETBOT_DIR` variable in each script before copying
- These are convenience wrappers - you can still use the scripts directly from the jetbot-orin directory
- JetBot containers use significant GPU memory (~2-3GB) - stop them before running jetbot-rover VILA service

## Memory Management

⚠️ **Important**: JetBot containers and VILA service both use GPU memory:
- JetBot containers: ~2-3GB GPU memory
- VILA service: ~4.3GB GPU memory
- **Total available**: 8GB on Jetson Orin Nano

**Best practice**:
- Stop JetBot containers before running VILA: `~/stop_jetbot.sh`
- Stop VILA before running JetBot containers: `docker stop vila-service`
- Or use collision avoidance only mode (no VILA): `~/run_collision_avoidance.sh`

## Troubleshooting

**Containers won't start**:
```bash
# Check if containers are already running
docker ps

# Check Docker logs
docker logs jetbot_jupyter
docker logs jetbot_display
```

**Out of GPU memory**:
```bash
# Check GPU memory usage
nvidia-smi

# Stop VILA service to free GPU memory
docker stop vila-service

# Or stop JetBot containers
~/stop_jetbot.sh
```

**Camera not working**:
```bash
# Restart nvargus daemon
sudo systemctl restart nvargus-daemon

# Check power mode
sudo nvpmodel -q  # Should be mode 2 (MAXN)
```
