# Project NVIDIA Jetbot (Orin Nano)

For more information on this project, visit: https://www.protomota.com/blog/jetbot-orin

## Quick Start

Simple startup and shutdown scripts for managing JetBot Docker containers.

### Starting JetBot Services

To start all JetBot Docker containers:

```bash
./start.sh [workspace_path] [camera_type]
```

Parameters:
- `workspace_path` (optional): Path to workspace directory (default: `$HOME`)
- `camera_type` (optional): `opencv_gst_camera` (default) or `zmq_camera`

Example:
```bash
./start.sh                    # Use defaults
./start.sh $HOME zmq_camera   # Use ZMQ camera
```

After starting, access Jupyter Lab at `https://<jetbot_ip>:8888` (password: `jetbot`)

### Stopping JetBot Services

To stop and remove all JetBot containers:

```bash
./stop.sh
```

### Manual Docker Commands

View running containers:
```bash
docker ps
```

View container logs:
```bash
docker logs -f jetbot_jupyter
docker logs -f jetbot_display
```

Restart a specific container:
```bash
docker restart jetbot_jupyter
```
