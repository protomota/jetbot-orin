#!/usr/bin/env python3
"""
Gamepad diagnostic script - shows all axes and button values.
Use this to determine the correct axis mappings for your controller.
"""

import pygame
import sys
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No gamepad detected.")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Gamepad: {joystick.get_name()}")
print(f"Axes: {joystick.get_numaxes()}")
print(f"Buttons: {joystick.get_numbuttons()}\n")
print("Move sticks and press buttons to see values. Press Ctrl+C to exit.\n")

try:
    while True:
        pygame.event.pump()

        # Print all axis values
        axes_str = "Axes: "
        for i in range(joystick.get_numaxes()):
            value = joystick.get_axis(i)
            axes_str += f"[{i}]:{value:6.3f} "

        # Print all button values
        buttons_str = "Buttons: "
        for i in range(joystick.get_numbuttons()):
            value = joystick.get_button(i)
            if value:
                buttons_str += f"[{i}] "

        print(f"\r{axes_str} | {buttons_str}     ", end='', flush=True)
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n\nExiting...")
    pygame.quit()
