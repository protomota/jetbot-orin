#!/usr/bin/env python3
"""
Bluetooth gamepad control with web interface for JetBot.

This script allows you to control the JetBot using a Bluetooth gamepad
and provides a web interface to view captured photos and controller status.

Controls:
- Left stick vertical axis: Left motor
- Right stick vertical axis: Right motor
- L1 (left shoulder): Capture photo to ~/training-photos/left/
- R1 (right shoulder): Capture photo to ~/training-photos/right/
- Start/Options button: Exit

Web Interface:
- http://<jetbot-ip>:5000 - View photos and controller status

Requirements:
- pygame library: pip3 install pygame
- flask library: pip3 install flask
"""

import pygame
import sys
import time
import os
import subprocess
import threading
from datetime import datetime
from jetbot import Robot
import cv2
import numpy as np
from flask import Flask, render_template, jsonify, send_from_directory, Response

# Global state
app = Flask(__name__)
state = {
    'running': False,
    'camera_available': False,
    'gamepad_connected': False,
    'gamepad_name': '',
    'left_motor': 0.0,
    'right_motor': 0.0,
    'left_count': 0,
    'right_count': 0,
    'left_axis': 0.0,
    'right_axis': 0.0,
    'last_photo': None,
    'last_photo_side': None,
    'message': ''
}

photo_base_dir = os.path.expanduser("~/training-photos")
left_dir = os.path.join(photo_base_dir, "left")
right_dir = os.path.join(photo_base_dir, "right")

# Global camera reference for video feed
global_camera = None


class GStreamerCamera:
    """GStreamer camera using persistent pipeline for low latency"""
    def __init__(self):
        self.last_capture_time = 0
        self.min_capture_interval = 0.5
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.running = False
        self.stream_process = None

    def start(self):
        """Start the camera capture thread"""
        try:
            print("Starting camera pipeline...")

            # Start persistent GStreamer pipeline that outputs to stdout
            gst_cmd = [
                'gst-launch-1.0', '-q',
                'nvarguscamerasrc', '!',
                'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1', '!',
                'nvvidconv', '!',
                'video/x-raw,width=640,height=480', '!',
                'videoconvert', '!',
                'video/x-raw,format=BGR', '!',
                'fdsink'
            ]

            self.stream_process = subprocess.Popen(
                gst_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=640*480*3
            )

            # Start frame reading thread
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()

            time.sleep(1)
            print("Camera pipeline started")
            return True

        except Exception as e:
            print(f"Camera start error: {e}")
            return False

    def _capture_loop(self):
        """Continuously read frames from GStreamer stdout"""
        frame_size = 640 * 480 * 3  # BGR format

        while self.running and self.stream_process:
            try:
                # Read one frame worth of data
                raw_frame = self.stream_process.stdout.read(frame_size)

                if len(raw_frame) != frame_size:
                    continue

                # Convert raw bytes to numpy array
                frame = np.frombuffer(raw_frame, dtype=np.uint8)
                frame = frame.reshape((480, 640, 3))

                with self.frame_lock:
                    self.latest_frame = frame.copy()

            except Exception as e:
                if self.running:
                    print(f"Frame read error: {e}")
                break

    def get_frame(self):
        """Get the latest frame"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
        return None

    def capture(self, filename):
        """Capture current frame to file"""
        current_time = time.time()
        if current_time - self.last_capture_time < self.min_capture_interval:
            print(f"Capture too soon (rate limited)")
            return False

        frame = self.get_frame()
        if frame is None:
            print(f"No frame available for capture")
            return False

        try:
            # Resize to 224x224 for training
            small_frame = cv2.resize(frame, (224, 224))
            success = cv2.imwrite(filename, small_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            if success:
                self.last_capture_time = current_time
                file_size = os.path.getsize(filename)
                print(f"Captured {filename}: {file_size} bytes")
                return True
            else:
                print(f"cv2.imwrite failed for {filename}")
            return False
        except Exception as e:
            print(f"Capture error: {e}")
            return False

    def stop(self):
        """Stop the camera process"""
        self.running = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=2)
        if self.stream_process:
            self.stream_process.terminate()
            try:
                self.stream_process.wait(timeout=2)
            except:
                self.stream_process.kill()


def robot_control_loop():
    """Main robot control loop running in separate thread"""
    global state, global_camera

    # Initialize pygame and joystick
    pygame.init()
    pygame.joystick.init()

    # Check for connected joysticks
    if pygame.joystick.get_count() == 0:
        state['message'] = "No gamepad detected"
        state['gamepad_connected'] = False
        return

    # Initialize the first joystick
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    state['gamepad_connected'] = True
    state['gamepad_name'] = joystick.get_name()
    state['message'] = f"Gamepad connected: {joystick.get_name()}"
    print(f"Gamepad connected: {joystick.get_name()}")

    # Initialize robot
    robot = Robot()
    robot.stop()

    # Initialize camera
    print("Initializing camera...")
    camera = GStreamerCamera()
    camera_available = camera.start()
    state['camera_available'] = camera_available
    global_camera = camera  # Store globally for video feed

    if camera_available:
        print("Camera initialized (using GStreamer)")
        state['message'] = "Camera and gamepad ready"
    else:
        print("Warning: Camera not available")
        state['message'] = "Gamepad ready, camera unavailable"

    # Create photo directories
    os.makedirs(left_dir, exist_ok=True)
    os.makedirs(right_dir, exist_ok=True)

    # Count existing photos
    left_photos = [f for f in os.listdir(left_dir) if f.endswith('.jpg')]
    right_photos = [f for f in os.listdir(right_dir) if f.endswith('.jpg')]
    state['left_count'] = len(left_photos)
    state['right_count'] = len(right_photos)
    print(f"Found {len(left_photos)} left photos, {len(right_photos)} right photos")

    # Deadzone to prevent drift from centered sticks
    DEADZONE = 0.1

    # Control loop
    state['running'] = True
    try:
        while state['running']:
            # Update joystick state
            pygame.event.pump()

            # Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state['running'] = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Button 4: L1 (left shoulder)
                    if event.button == 4:
                        if camera_available:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = os.path.join(left_dir, f"left_{timestamp}.jpg")
                            if camera.capture(filename):
                                state['left_count'] += 1
                                state['last_photo'] = f"left_{timestamp}.jpg"
                                state['last_photo_side'] = 'left'
                                state['message'] = f"LEFT photo saved ({state['left_count']} total)"
                                print(f"[LEFT] Photo saved: {filename}")
                            else:
                                state['message'] = "Too fast - wait 0.5s between photos"
                        else:
                            state['message'] = "Camera not available"

                    # Button 5: R1 (right shoulder)
                    elif event.button == 5:
                        if camera_available:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = os.path.join(right_dir, f"right_{timestamp}.jpg")
                            if camera.capture(filename):
                                state['right_count'] += 1
                                state['last_photo'] = f"right_{timestamp}.jpg"
                                state['last_photo_side'] = 'right'
                                state['message'] = f"RIGHT photo saved ({state['right_count']} total)"
                                print(f"[RIGHT] Photo saved: {filename}")
                            else:
                                state['message'] = "Too fast - wait 0.5s between photos"
                        else:
                            state['message'] = "Camera not available"

                    # Button 7: Start/Options button
                    elif event.button == 7:
                        print("Start button pressed. Exiting...")
                        state['running'] = False
                        state['message'] = "Shutting down..."

            # Read joystick axes
            left_value = -joystick.get_axis(1)  # Inverted
            right_value = -joystick.get_axis(5)  # Inverted

            # Apply deadzone
            if abs(left_value) < DEADZONE:
                left_value = 0.0
            if abs(right_value) < DEADZONE:
                right_value = 0.0

            # Update state
            state['left_axis'] = left_value
            state['right_axis'] = right_value
            state['left_motor'] = left_value
            state['right_motor'] = right_value

            # Set motor values
            robot.left_motor.value = left_value
            robot.right_motor.value = right_value

            # Small delay
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Keyboard interrupt detected")
        state['message'] = "Interrupted"

    finally:
        # Cleanup
        robot.stop()
        if camera_available:
            camera.stop()
        pygame.quit()
        state['running'] = False
        print("Robot control stopped")


# Flask routes
@app.route('/')
def index():
    """Main page"""
    return render_template('gamepad_control.html')


@app.route('/api/status')
def api_status():
    """Get current status"""
    return jsonify(state)


@app.route('/api/photos/<side>')
def api_photos(side):
    """Get list of photos for a side (left/right)"""
    if side not in ['left', 'right']:
        return jsonify({'error': 'Invalid side'}), 400

    photo_dir = left_dir if side == 'left' else right_dir
    if not os.path.exists(photo_dir):
        return jsonify({'photos': []})

    photos = sorted([f for f in os.listdir(photo_dir) if f.endswith('.jpg')], reverse=True)
    return jsonify({'photos': photos[:50]})  # Return latest 50


@app.route('/photos/<side>/<filename>')
def serve_photo(side, filename):
    """Serve a photo file"""
    if side not in ['left', 'right']:
        return "Invalid side", 400

    photo_dir = left_dir if side == 'left' else right_dir
    return send_from_directory(photo_dir, filename)


@app.route('/api/delete/<side>/<filename>', methods=['DELETE'])
def api_delete_photo(side, filename):
    """Delete a single photo"""
    if side not in ['left', 'right']:
        return jsonify({'error': 'Invalid side'}), 400

    photo_dir = left_dir if side == 'left' else right_dir
    file_path = os.path.join(photo_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'Photo not found'}), 404

    try:
        os.remove(file_path)
        # Update counters
        if side == 'left':
            state['left_count'] = max(0, state['left_count'] - 1)
        else:
            state['right_count'] = max(0, state['right_count'] - 1)
        return jsonify({'status': 'deleted', 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete-all/<side>', methods=['DELETE'])
def api_delete_all_photos(side):
    """Delete all photos for a side"""
    if side not in ['left', 'right']:
        return jsonify({'error': 'Invalid side'}), 400

    photo_dir = left_dir if side == 'left' else right_dir
    if not os.path.exists(photo_dir):
        return jsonify({'status': 'no photos to delete'})

    try:
        count = 0
        for filename in os.listdir(photo_dir):
            if filename.endswith('.jpg'):
                os.remove(os.path.join(photo_dir, filename))
                count += 1

        # Reset counter
        if side == 'left':
            state['left_count'] = 0
        else:
            state['right_count'] = 0

        return jsonify({'status': 'deleted', 'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    """Shutdown the server"""
    state['running'] = False
    return jsonify({'status': 'shutting down'})


def generate_video_feed():
    """Generate video frames for MJPEG stream"""
    while True:
        if global_camera is None:
            time.sleep(0.1)
            continue

        frame = global_camera.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(0.033)  # ~30 fps


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_video_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def create_html_template():
    """Create the HTML template file"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(template_dir, exist_ok=True)

    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>JetBot Gamepad Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .top-section {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }
        .video-feed {
            background: #2a2a2a;
            padding: 10px;
            border-radius: 10px;
        }
        .video-feed img {
            width: 100%;
            max-width: 300px;
            border-radius: 5px;
        }
        .header {
            background: #2a2a2a;
            padding: 10px;
            border-radius: 10px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        .status-item {
            background: #333;
            padding: 8px;
            border-radius: 5px;
        }
        .status-label { font-size: 10px; color: #999; }
        .status-value { font-size: 16px; font-weight: bold; margin-top: 3px; }
        .motor-viz {
            height: 40px;
            background: #222;
            border-radius: 3px;
            position: relative;
            margin-top: 5px;
        }
        .motor-bar {
            position: absolute;
            bottom: 0;
            width: 100%;
            background: linear-gradient(to top, #4CAF50, #8BC34A);
            border-radius: 3px;
            transition: height 0.1s, background 0.2s;
        }
        .motor-bar.negative {
            background: linear-gradient(to top, #f44336, #e57373);
        }
        .photos-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        .photo-column {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
        }
        .photo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        .photo-item {
            aspect-ratio: 1;
            overflow: hidden;
            border-radius: 5px;
            background: #333;
            position: relative;
        }
        .photo-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            cursor: pointer;
        }
        .delete-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            background: rgba(244, 67, 54, 0.9);
            color: white;
            border: none;
            border-radius: 3px;
            padding: 5px 8px;
            cursor: pointer;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        }
        .photo-item:hover .delete-btn {
            opacity: 1;
        }
        .delete-btn:hover {
            background: rgba(244, 67, 54, 1);
        }
        .message {
            background: #333;
            padding: 8px;
            border-radius: 5px;
            margin-top: 8px;
            font-size: 11px;
        }
        h1 { margin: 0 0 10px 0; font-size: 18px; }
        .connected { color: #4CAF50; }
        .disconnected { color: #f44336; }
        h2 { margin-top: 0; display: inline-block; }
        .delete-all-btn {
            float: right;
            background: #f44336;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            cursor: pointer;
            font-size: 14px;
        }
        .delete-all-btn:hover {
            background: #d32f2f;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-section">
            <div class="video-feed">
                <h1>📹 Live Camera Feed</h1>
                <img src="/video_feed" alt="Live Feed" />
            </div>
            <div class="header">
                <h1>🎮 Status</h1>
                <div class="status-grid">
                    <div class="status-item">
                        <div class="status-label">Gamepad</div>
                        <div class="status-value" id="gamepad-status">-</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Camera</div>
                        <div class="status-value" id="camera-status">-</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Left Photos</div>
                        <div class="status-value" id="left-count">0</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Right Photos</div>
                        <div class="status-value" id="right-count">0</div>
                    </div>
                </div>
                <div class="status-grid" style="margin-top: 8px;">
                    <div class="status-item">
                        <div class="status-label">Left Motor</div>
                        <div class="motor-viz">
                            <div class="motor-bar" id="left-motor-bar"></div>
                        </div>
                        <div style="text-align: center; margin-top: 3px; font-size: 11px;" id="left-motor-val">0.00</div>
                    </div>
                    <div class="status-item">
                        <div class="status-label">Right Motor</div>
                        <div class="motor-viz">
                            <div class="motor-bar" id="right-motor-bar"></div>
                        </div>
                        <div style="text-align: center; margin-top: 3px; font-size: 11px;" id="right-motor-val">0.00</div>
                    </div>
                </div>
                <div class="message" id="message">Waiting...</div>
            </div>
        </div>

        <div class="photos-section">
            <div class="photo-column">
                <h2>⬅️ Left Photos</h2>
                <button class="delete-all-btn" onclick="deleteAll('left')">🗑️ Delete All Left</button>
                <div style="clear: both;"></div>
                <div class="photo-grid" id="left-photos"></div>
            </div>
            <div class="photo-column">
                <h2>➡️ Right Photos</h2>
                <button class="delete-all-btn" onclick="deleteAll('right')">🗑️ Delete All Right</button>
                <div style="clear: both;"></div>
                <div class="photo-grid" id="right-photos"></div>
            </div>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('gamepad-status').innerHTML =
                        data.gamepad_connected ?
                        `<span class="connected">✓ ${data.gamepad_name}</span>` :
                        '<span class="disconnected">✗ Not connected</span>';

                    document.getElementById('camera-status').innerHTML =
                        data.camera_available ?
                        '<span class="connected">✓ Ready</span>' :
                        '<span class="disconnected">✗ Not available</span>';

                    document.getElementById('left-count').textContent = data.left_count;
                    document.getElementById('right-count').textContent = data.right_count;
                    document.getElementById('message').textContent = data.message;

                    // Update motor visualizations
                    const leftPct = Math.abs(data.left_motor) * 100;
                    const rightPct = Math.abs(data.right_motor) * 100;
                    const leftBar = document.getElementById('left-motor-bar');
                    const rightBar = document.getElementById('right-motor-bar');

                    leftBar.style.height = leftPct + '%';
                    rightBar.style.height = rightPct + '%';

                    // Add/remove negative class for color change
                    if (data.left_motor < 0) {
                        leftBar.classList.add('negative');
                    } else {
                        leftBar.classList.remove('negative');
                    }

                    if (data.right_motor < 0) {
                        rightBar.classList.add('negative');
                    } else {
                        rightBar.classList.remove('negative');
                    }

                    document.getElementById('left-motor-val').textContent = data.left_motor.toFixed(2);
                    document.getElementById('right-motor-val').textContent = data.right_motor.toFixed(2);
                });
        }

        function deletePhoto(side, filename) {
            fetch(`/api/delete/${side}/${filename}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'deleted') {
                        loadPhotos(side);
                    } else {
                        alert('Error deleting photo: ' + (data.error || 'Unknown error'));
                    }
                });
        }

        function deleteAll(side) {
            const sideName = side === 'left' ? 'LEFT' : 'RIGHT';
            if (!confirm(`Delete ALL ${sideName} photos? This cannot be undone!`)) return;

            fetch(`/api/delete-all/${side}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'deleted') {
                        loadPhotos(side);
                        alert(`Deleted ${data.count} ${sideName} photos`);
                    } else {
                        alert('Error: ' + (data.error || 'Unknown error'));
                    }
                });
        }

        function loadPhotos(side) {
            fetch(`/api/photos/${side}`)
                .then(r => r.json())
                .then(data => {
                    const grid = document.getElementById(`${side}-photos`);
                    grid.innerHTML = data.photos.map(photo =>
                        `<div class="photo-item">
                            <img src="/photos/${side}/${photo}" alt="${photo}"
                                 onclick="window.open(this.src, '_blank')">
                            <button class="delete-btn" onclick="event.stopPropagation(); deletePhoto('${side}', '${photo}')">✕</button>
                        </div>`
                    ).join('');
                });
        }

        // Update status every 500ms (reduced from 100ms to minimize logs)
        setInterval(updateStatus, 500);

        // Update photos every 3 seconds
        setInterval(() => {
            loadPhotos('left');
            loadPhotos('right');
        }, 3000);

        // Initial load
        updateStatus();
        loadPhotos('left');
        loadPhotos('right');
    </script>
</body>
</html>'''

    with open(os.path.join(template_dir, 'gamepad_control.html'), 'w') as f:
        f.write(html_content)


def main():
    """Main entry point"""
    print("JetBot Gamepad Control with Web Interface")
    print("=" * 50)

    # Create HTML template
    create_html_template()

    # Disable Flask's default request logging to reduce spam
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Start robot control in separate thread
    control_thread = threading.Thread(target=robot_control_loop, daemon=True)
    control_thread.start()

    # Wait a moment for initialization
    time.sleep(2)

    # Get IP address
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    print(f"\nWeb interface available at:")
    print(f"  http://{ip_address}:5000")
    print(f"  http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")

    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    main()
