# Jetson Orin Nano IMX219 Camera Setup Guide

This guide covers the complete setup process for getting an ArduCam IMX219 camera working on the NVIDIA Jetson Orin Nano.

## Hardware
- NVIDIA Jetson Orin Nano
- ArduCam 8MP IMX219 175 Degree Ultra Wide Angle Camera for Raspberry Pi
- Camera connected to CAM0 connector

## Initial Setup

### 1. Install Required Tools
```bash
sudo apt update
sudo apt install v4l-utils
```

### 2. Configure Camera Device Tree
Run the jetson-io configuration tool:
```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```

Steps:
1. Select "Configure Jetson 24pin CSI Connector"
2. Select "Camera IMX219-A" (for single camera on CAM0)
3. Save the configuration
4. Reboot the system

```bash
sudo reboot
```

### 3. Verify Camera Detection
After reboot, check if the camera is detected:
```bash
# Check i2c bus for camera (should show UU at address 0x10)
sudo i2cdetect -y -r 9

# Check kernel messages
sudo dmesg | grep -i imx219

# Check for video device
ls /dev/video*
```

### 4. Update System (Important for Bug Fixes)
The initial JetPack version had a driver bug. Update to fix it:
```bash
sudo apt update
sudo apt upgrade
sudo reboot
```

After update, re-run jetson-io to reconfigure the camera (the update resets device tree):
```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
# Select "Configure Jetson 24pin CSI Connector" > "Camera IMX219-A"
# Save and reboot
sudo reboot
```

### 5. Set Power Mode to Maximum
```bash
# Set to 25W mode
sudo /usr/sbin/nvpmodel -m 0

# Set clocks to maximum
sudo jetson_clocks

# Verify power mode
sudo /usr/sbin/nvpmodel -q
```

## Testing the Camera

### Capture Still Images
```bash
# Capture 10 JPEG images at 720p
gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=10 ! 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=60/1' ! nvjpegenc ! multifilesink location=test_%03d.jpg
```

### Record Video
```bash
# Record video to MP4 file
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=60/1' ! nvvidconv ! 'video/x-raw(memory:NVMM),format=I420' ! nvv4l2h264enc ! h264parse ! mp4mux ! filesink location=test_video.mp4
```

## Web Streaming Server Setup

### Create Project Directory
```bash
mkdir -p ~/source/jetson-source/jetson-camera
cd ~/source/jetson-source/jetson-camera
```

### Set Up Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install Flask
pip install flask
```

### Create Camera Server
Create `camera_server.py` with the following content:

```python
from flask import Flask, Response
import subprocess

app = Flask(__name__)

def generate_frames():
    # GStreamer pipeline that outputs JPEG frames
    gst_cmd = [
        'gst-launch-1.0',
        '-q',
        'nvarguscamerasrc', 'sensor-id=0',
        '!', 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1',
        '!', 'nvvidconv',
        '!', 'nvjpegenc',
        '!', 'fdsink'
    ]
    
    print(f"Starting GStreamer pipeline...")
    process = subprocess.Popen(gst_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)
    
    try:
        while True:
            # Read JPEG marker
            marker = process.stdout.read(2)
            if len(marker) != 2 or marker != b'\xff\xd8':
                continue
                
            # Read until end of JPEG
            jpeg_data = marker
            while True:
                byte = process.stdout.read(1)
                if not byte:
                    break
                jpeg_data += byte
                if len(jpeg_data) >= 2 and jpeg_data[-2:] == b'\xff\xd9':
                    break
            
            if len(jpeg_data) > 100:  # Valid JPEG
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
    finally:
        process.terminate()
        process.wait()

@app.route('/')
def index():
    return '''
    <html>
      <head><title>Orin Camera Stream</title></head>
      <body style="margin:0; padding:0; background:#000;">
        <h1 style="color:#fff; text-align:center;">Jetson Camera Stream</h1>
        <div style="text-align:center;">
          <img src="/video_feed" style="max-width:100%; height:auto;">
        </div>
      </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
```

### Run the Server
```bash
cd ~/source/jetson-source/jetson-camera
source venv/bin/activate
python camera_server.py
```

Access the stream at: `http://<orin-ip-address>:5000`

To stop: Press `Ctrl+C`

To deactivate virtual environment:
```bash
deactivate
```

## Available Camera Modes

The IMX219 supports these modes:
- 3280 x 2464 @ 21 fps (full resolution)
- 3280 x 1848 @ 28 fps
- 1920 x 1080 @ 30 fps
- 1640 x 1232 @ 30 fps
- 1280 x 720 @ 60 fps

## Troubleshooting

### Camera Not Detected
```bash
# Check physical connection - reseat ribbon cable
# Ensure metal contacts face DOWN toward the board
# Blue tab should face UP

# Check i2c detection
sudo i2cdetect -y -r 9

# Check kernel logs
sudo dmesg | grep -i imx219
```

### Camera Detected But Won't Stream
- Ensure system is updated to latest JetPack version
- Verify device tree is configured (re-run jetson-io after updates)
- Check power mode is set to maximum (25W)
- Verify cable connection is secure

### Display Issues
The camera works for capture but may have issues with live display using eglglessink. Use file capture or the web server for viewing.

## System Information
- Tested on: JetPack 6.1 (R36.4.7)
- Camera: ArduCam IMX219 8MP 175° Wide Angle
- Board: Jetson Orin Nano
