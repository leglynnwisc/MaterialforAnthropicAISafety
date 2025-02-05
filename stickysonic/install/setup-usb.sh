#!/bin/bash

echo "Sticky Sonic - USB Installation"
echo "-------------------------------"

# Find USB drive (assuming it's mounted)
USB_PATH=$(lsblk -o MOUNTPOINT | grep "/media/pi" | head -n 1)

if [ -z "$USB_PATH" ]; then
    echo "No USB drive found. Please insert a USB drive and try again."
    exit 1
fi

# Copy files from USB to Pi
echo "Copying files from USB..."
cp -r "$USB_PATH/field-recorder" /home/pi/

# Run common installation steps
cd /home/pi/field-recorder
./install/setup-common.sh