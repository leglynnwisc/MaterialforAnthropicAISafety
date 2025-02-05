#!/bin/bash

echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-tk ffmpeg v4l-utils libportaudio2 \
    python3-pil python3-pil.imagetk python3-picamera2 libcamera0 python3-libcamera

# Install Python packages
sudo pip3 install -r install/requirements.txt

echo "Setting up camera..."
# Enable camera in raspi-config
sudo raspi-config nonint do_camera 0

# Test camera setup
echo "Testing camera setup..."
python3 /home/pi/stickysonic/tools/test_camera.py
CAMERA_TEST_RESULT=$?

if [ $CAMERA_TEST_RESULT -ne 0 ]; then
    echo "Warning: Camera test failed. Check logs for details."
    echo "You may need to:"
    echo "1. Ensure the camera is properly connected"
    echo "2. Reboot the system if camera was just enabled"
    echo "3. Run 'python3 /home/pi/stickysonic/tools/test_camera.py' again after fixing issues"
    read -p "Continue with setup anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Setting up services..."
# Copy systemd service files
sudo cp systemd/sticky-sonic-gui.service /etc/systemd/system/
sudo cp systemd/sticky-sonic.service /etc/systemd/system/
sudo cp systemd/sticky-sonic.timer /etc/systemd/system/

# Set permissions
chmod +x src/gui.py
chmod +x src/recorder.py
chmod +x tools/test_camera.py
chmod +x tools/check_mics.py

# Create necessary directories
mkdir -p /home/pi/stickysonic/logs
mkdir -p /home/pi/stickysonic/recordings
mkdir -p /home/pi/stickysonic/camera_test
touch /home/pi/stickysonic/logs/app.log
chown -R pi:pi /home/pi/stickysonic

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable sticky-sonic-gui.service
sudo systemctl start sticky-sonic-gui.service

echo "Installation complete!"
if [ $CAMERA_TEST_RESULT -eq 0 ]; then
    echo "Camera setup and testing successful."
else
    echo "Warning: Camera setup needs attention. Check logs and run test_camera.py after fixing issues."
fi
echo "The Sticky Sonic GUI should start automatically on next boot."
echo "To start now, run: sudo systemctl start sticky-sonic-gui"