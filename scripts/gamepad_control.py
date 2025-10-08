#!/usr/bin/env python3
"""
Bluetooth gamepad control script for JetBot.

This script allows you to control the JetBot using a Bluetooth gamepad
connected directly to the Jetson Nano.

Controls:
- Left stick vertical axis: Left motor
- Right stick vertical axis: Right motor
- Start/Options button: Exit

Requirements:
- pygame library: pip3 install pygame
"""

import pygame
import sys
import time
from jetbot import Robot


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
    print("  Start/Options button: Exit")
    print("\nReady to control robot. Press Ctrl+C or Start button to exit.\n")

    # Initialize robot
    robot = Robot()

    # Ensure motors are stopped on startup
    robot.stop()

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
                    # Button 7 is typically the Start/Options button
                    if event.button == 7:
                        print("Start button pressed. Exiting...")
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

        # Cleanup
        pygame.quit()


if __name__ == "__main__":
    main()
