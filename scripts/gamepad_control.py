#!/usr/bin/env python3
"""
Bluetooth gamepad control script for JetBot.

This script allows you to control the JetBot using a Bluetooth gamepad
connected directly to the Jetson Nano.

Controls:
- Left stick vertical axis: Left motor
- Right stick vertical axis: Right motor
- L1 (left shoulder): Capture photo to ~/training-photos/left/
- R1 (right shoulder): Capture photo to ~/training-photos/right/
- Start/Options button: Exit

Requirements:
- pygame library: pip3 install pygame
"""

import pygame
import sys
import time
import os
import subprocess
from datetime import datetime
from jetbot import Robot
import cv2


class GStreamerCamera:
    """Persistent GStreamer camera that stays open for fast captures"""
    def __init__(self):
        self.process = None
        self.last_capture_time = 0
        self.min_capture_interval = 0.5  # Minimum time between captures in seconds

    def start(self):
        """Start the camera process"""
        # Use a simple v4l2 pipeline that's more reliable
        gst_cmd = [
            'gst-launch-1.0', '-q',
            'nvarguscamerasrc',
            '!', 'video/x-raw(memory:NVMM),width=1640,height=1232,framerate=30/1,format=NV12',
            '!', 'nvvidconv',
            '!', 'video/x-raw,width=224,height=224',
            '!', 'identity', 'name=snapshot',
            '!', 'fakesink'
        ]
        try:
            # Start a persistent pipeline
            self.process = subprocess.Popen(gst_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)  # Give it time to initialize
            return True
        except:
            return False

    def capture(self, filename):
        """Capture a single frame to file"""
        current_time = time.time()
        if current_time - self.last_capture_time < self.min_capture_interval:
            return False

        gst_cmd = [
            'gst-launch-1.0', '-q',
            'nvarguscamerasrc', 'num-buffers=1',
            '!', 'video/x-raw(memory:NVMM),width=1640,height=1232,framerate=30/1',
            '!', 'nvvidconv',
            '!', 'video/x-raw,width=224,height=224',
            '!', 'jpegenc',
            '!', 'filesink', f'location={filename}'
        ]
        try:
            result = subprocess.run(gst_cmd, capture_output=True, timeout=3, check=True)
            self.last_capture_time = current_time
            return True
        except:
            return False

    def stop(self):
        """Stop the camera process"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except:
                self.process.kill()


def main():
    # Initialize pygame and joystick
    pygame.init()
    pygame.joystick.init()

    # Check for connected joysticks
    if pygame.joystick.get_count() == 0:
        print("No gamepad detected. Please connect a gamepad and try again.")
        sys.exit(1)

    # Initialize the first joystick
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    print(f"Gamepad connected: {joystick.get_name()}")
    print(f"Number of axes: {joystick.get_numaxes()}")
    print(f"Number of buttons: {joystick.get_numbuttons()}")
    print("\nControls:")
    print("  Left stick (vertical): Left motor")
    print("  Right stick (vertical): Right motor")
    print("  L1 (left shoulder): Capture photo to ~/training-photos/left/")
    print("  R1 (right shoulder): Capture photo to ~/training-photos/right/")
    print("  Start/Options button: Exit")
    print("\nReady to control robot. Press Ctrl+C or Start button to exit.\n")

    # Initialize robot
    robot = Robot()

    # Ensure motors are stopped on startup
    robot.stop()

    # Initialize camera
    print("Initializing camera...")
    camera = GStreamerCamera()
    camera_available = camera.start()
    if camera_available:
        print("Camera initialized (using GStreamer)")
    else:
        print("Warning: Camera not available. Photo capture will be disabled.")
        camera = None

    # Create photo directories
    photo_base_dir = os.path.expanduser("~/training-photos")
    left_dir = os.path.join(photo_base_dir, "left")
    right_dir = os.path.join(photo_base_dir, "right")
    os.makedirs(left_dir, exist_ok=True)
    os.makedirs(right_dir, exist_ok=True)
    print(f"Photos will be saved to: {photo_base_dir}")

    # Photo counters
    left_count = 0
    right_count = 0

    # Deadzone to prevent drift from centered sticks
    DEADZONE = 0.1

    # Control loop
    running = True
    try:
        while running:
            # Update joystick state
            pygame.event.pump()
            # Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Button 4: L1 (left shoulder)
                    if event.button == 4:
                        if camera_available:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = os.path.join(left_dir, f"left_{timestamp}.jpg")
                            if camera.capture(filename):
                                left_count += 1
                                print(f"\n[LEFT] Photo saved: {filename} (Total: {left_count})")
                            else:
                                print("\n[LEFT] Too fast - wait 0.5s between photos")
                        else:
                            print("\n[LEFT] Camera not available - cannot capture photo")

                    # Button 5: R1 (right shoulder)
                    elif event.button == 5:
                        if camera_available:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                            filename = os.path.join(right_dir, f"right_{timestamp}.jpg")
                            if camera.capture(filename):
                                right_count += 1
                                print(f"\n[RIGHT] Photo saved: {filename} (Total: {right_count})")
                            else:
                                print("\n[RIGHT] Too fast - wait 0.5s between photos")
                        else:
                            print("\n[RIGHT] Camera not available - cannot capture photo")

                    # Button 7: Start/Options button
                    elif event.button == 7:
                        print("\nStart button pressed. Exiting...")
                        running = False

            # Read joystick axes
            # Axis 1: Left stick vertical (up/down)
            # Axis 5: Right stick vertical (up/down)
            left_value = -joystick.get_axis(1)  # Inverted to match intuitive control
            right_value = -joystick.get_axis(5)  # Inverted to match intuitive control

            # Apply deadzone
            if abs(left_value) < DEADZONE:
                left_value = 0.0
            if abs(right_value) < DEADZONE:
                right_value = 0.0

            # Debug output
            print(f"\rLeft: {left_value:6.3f}  Right: {right_value:6.3f}  Motor L: {robot.left_motor.value:6.3f}  Motor R: {robot.right_motor.value:6.3f}", end='', flush=True)

            # Set motor values
            robot.left_motor.value = left_value
            robot.right_motor.value = right_value

            # Small delay to prevent CPU overuse
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Stopping robot...")

    finally:
        # Stop the robot
        robot.stop()
        print("Robot stopped.")

        # Stop camera
        if camera_available and camera:
            camera.stop()
            print("Camera stopped.")

        # Print summary
        print(f"\nPhoto summary: Left={left_count}, Right={right_count}, Total={left_count + right_count}")

        # Cleanup
        pygame.quit()


if __name__ == "__main__":
    main()
