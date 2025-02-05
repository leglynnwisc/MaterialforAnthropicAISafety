import sounddevice as sd
import json
import os
from colorama import init, Fore, Style


def check_mic_setup():
    """Check and display microphone setup from terminal"""
    init()  # Initialize colorama for colored output

    print("\nSticky Sonic Microphone Setup Check")
    print("=================================")

    try:
        # Load configuration
        with open('/home/pi/stickysonic/mic_config.json', 'r') as f:
            config = json.load(f)

        # Get current devices
        devices = sd.query_devices()

        # Check individual mics
        if 'individual_mics' in config:
            print("\nIndividual Microphones:")
            print("---------------------")
            for mic in config['individual_mics']:
                try:
                    device = devices[mic['id']]
                    if 'USB' in str(device):
                        status = f"{Fore.GREEN}✓ Connected{Style.RESET_ALL}"
                    else:
                        status = f"{Fore.RED}✗ Missing{Style.RESET_ALL}"

                    print(f"\n{mic['label']}:")
                    print(f"  Status: {status}")
                    print(f"  USB Path: {mic['usb_path']}")
                    print(f"  Device Name: {device.get('name', 'Unknown')}")
                except (KeyError, IndexError):
                    print(f"\n{mic['label']}:")
                    print(f"  Status: {Fore.RED}✗ Not Found{Style.RESET_ALL}")

        # Check multichannel devices
        if 'multichannel_devices' in config:
            print("\nMultichannel Devices:")
            print("-------------------")
            for device in config['multichannel_devices']:
                print(f"\n{device['name']}:")
                try:
                    current_device = devices[device['id']]
                    if 'USB' in str(current_device):
                        status = f"{Fore.GREEN}✓ Connected{Style.RESET_ALL}"
                    else:
                        status = f"{Fore.RED}✗ Missing{Style.RESET_ALL}"

                    print(f"  Status: {status}")
                    print(f"  USB Path: {device['usb_path']}")
                    print("\n  Channel Map:")
                    for ch, label in device['channel_labels'].items():
                        print(f"    Channel {int(ch) + 1}: {label}")
                except (KeyError, IndexError):
                    print(f"  Status: {Fore.RED}✗ Not Found{Style.RESET_ALL}")

    except FileNotFoundError:
        print(f"{Fore.YELLOW}No microphone configuration found.")
        print("Run 'python3 mic_mapper.py' to configure.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error checking mic setup: {str(e)}{Style.RESET_ALL}")


if __name__ == "__main__":
    check_mic_setup()