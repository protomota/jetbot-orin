#!/usr/bin/env python3
"""Simple motor test script for JetBot"""
import os
os.environ['JETBOT_I2C_BUS'] = '7'  # Set before importing jetbot

from jetbot import Robot
import time

print('Testing JetBot motors...')
robot = Robot()

print('Forward...')
robot.forward(0.3)
time.sleep(1)

print('Backward...')
robot.backward(0.3)
time.sleep(1)

print('Left...')
robot.left(0.3)
time.sleep(1)

print('Right...')
robot.right(0.3)
time.sleep(1)

print('Stop.')
robot.stop()
print('✓ Motor test complete!')
