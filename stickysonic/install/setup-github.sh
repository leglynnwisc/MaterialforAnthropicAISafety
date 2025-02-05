#!/bin/bash

echo "Sticky Sonic - GitHub Installation"
echo "----------------------------------"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt-get update
    sudo apt-get install -y git
fi

# Clone the repository
echo "Cloning Sticky Sonic repository..."
git clone https://github.com/yourusername/field-recorder.git /home/pi/field-recorder

# Run common installation steps
cd /home/pi/field-recorder
./install/setup-common.sh