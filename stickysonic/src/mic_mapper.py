#!/usr/bin/env python3

import sounddevice as sd
import json
import os


def map_microphones():
    """Simple utility to map microphones. Run once during setup."""
    print("\nMicrophone Mapping Utility")
    print("--------------------------")

    devices = sd.query_devices()
    usb_mics = []

    # Find USB microphones
    for i, device in enumerate(devices):
        if 'USB' in str(device) and device.get('max_input_channels', 0) > 0:
            name = device.get('name', f'USB Device {i}')
            print(f"\nFound USB Microphone:")
            print(f"ID: {i}")
            print(f"Name: {name}")

            label = input("Enter position label (e.g., left, right, center): ").strip()
            if label:
                usb_mics.append({
                    'id': i,
                    'name': name,
                    'label': label
                })

    # Save to simple JSON file
    config_path = '/home/pi/stickysonic/mic_config.json'
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(usb_mics, f, indent=2)

    print("\nMicrophone mapping saved!")
    print("Please label your USB cables with their positions.")


if __name__ == "__main__":
    map_microphones()