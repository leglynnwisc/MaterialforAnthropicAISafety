#!/bin/bash

# Script to set up Python development environment on a fresh Raspberry Pi

echo "Setting up Python Development Environment"
echo "======================================="

# Function to check if a command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo "✓ Success: $1"
    else
        echo "✗ Error: $1 failed"
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Update system
echo -e "\n1. Updating system packages..."
sudo apt update
sudo apt upgrade -y
check_status "System update"

# Install Python basics
echo -e "\n2. Installing Python and basic dependencies..."
sudo apt install -y python3 python3-pip python3-dev
check_status "Python basics installation"

# Install build essentials
echo -e "\n3. Installing build essentials..."
sudo apt install -y build-essential libssl-dev libffi-dev
check_status "Build essentials installation"

# Install development tools
echo -e "\n4. Installing development tools..."
sudo apt install -y git thonny
check_status "Development tools installation"

# Install virtual environment tools
echo -e "\n5. Installing Python virtual environment tools..."
sudo apt install -y python3-venv python3-virtualenv
check_status "Virtual environment tools installation"

# Install audio/visual dependencies
echo -e "\n6. Installing audio/visual libraries..."
sudo apt install -y python3-tk python3-picamera2 python3-libcamera
sudo apt install -y portaudio19-dev python3-dev
sudo apt install -y libportaudio2 libasound-dev
check_status "Audio/visual libraries installation"

# Create a Python virtual environment (optional)
echo -e "\n7. Would you like to create a Python virtual environment?"
read -p "Create virtual environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter name for virtual environment (default: 'venv'): " venv_name
    venv_name=${venv_name:-venv}
    python3 -m venv ~/$venv_name
    check_status "Virtual environment creation"
    echo -e "\nTo activate virtual environment:"
    echo "source ~/$venv_name/bin/activate"
fi

# Verify installations
echo -e "\n8. Verifying installations..."
echo "Python version:"
python3 --version
echo "Pip version:"
pip3 --version

# Create a simple Python test script
echo -e "\n9. Creating test script..."
cat > ~/test_python.py << EOL
# Test basic Python functionality
print("Basic Python test...")

# Test tkinter
try:
    import tkinter
    print("✓ Tkinter imported successfully")
except ImportError as e:
    print("✗ Tkinter import failed:", e)

# Test audio
try:
    import pyaudio
    print("✓ PyAudio imported successfully")
except ImportError as e:
    print("✗ PyAudio import failed:", e)

# Test camera
try:
    from picamera2 import Picamera2
    print("✓ PiCamera2 imported successfully")
except ImportError as e:
    print("✗ PiCamera2 import failed:", e)

print("\nTest complete!")
EOL

echo -e "\nSetup complete!"
echo "=================="
echo -e "\nTo test your Python installation, run:"
echo "python3 ~/test_python.py"
echo -e "\nRecommended next steps:"
echo "1. Start Thonny IDE: thonny"
echo "2. Create a virtual environment for your projects"
echo "3. Install any additional packages you need with pip3"