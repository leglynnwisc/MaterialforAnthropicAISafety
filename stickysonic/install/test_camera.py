#!/usr/bin/env python3

import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import json

try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FileOutput
except ImportError:
    print("Error: picamera2 not installed. Installing required packages...")
    subprocess.run(['sudo', 'apt-get', 'update'], check=True)
    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'python3-picamera2'], check=True)
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import FileOutput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CameraTest:
    def __init__(self):
        self.test_dir = Path('/home/pi/stickysonic/camera_test')
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.picam = None
        self.camera_info = {}

    def check_camera_enabled(self):
        """Check if camera is enabled in raspi-config"""
        try:
            result = subprocess.run(['vcgencmd', 'get_camera'],
                                    capture_output=True, text=True)
            if 'detected=1' not in result.stdout:
                print("Camera not detected. Enabling camera...")
                subprocess.run(['sudo', 'raspi-config', 'nonint', 'do_camera', '0'],
                               check=True)
                print("Camera enabled. System restart required.")
                return False
            return True
        except Exception as e:
            logging.error(f"Error checking camera status: {e}")
            return False

    def get_camera_info(self):
        """Get detailed camera information"""
        try:
            # Get camera model info
            v4l2_output = subprocess.run(['v4l2-ctl', '--list-devices'],
                                         capture_output=True, text=True).stdout

            # Get camera capabilities
            caps_output = subprocess.run(['v4l2-ctl', '--list-formats-ext'],
                                         capture_output=True, text=True).stdout

            self.camera_info = {
                'device_info': v4l2_output.strip(),
                'capabilities': caps_output.strip(),
                'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            return True
        except Exception as e:
            logging.error(f"Error getting camera info: {e}")
            return False

    def test_camera(self):
        """Run comprehensive camera test"""
        print("\nStarting Camera Test")
        print("===================")

        # Step 1: Check if camera is enabled
        print("\n1. Checking camera status...")
        if not self.check_camera_enabled():
            return False

        # Step 2: Get camera information
        print("\n2. Getting camera information...")
        if not self.get_camera_info():
            return False

        # Check if it's an IMX519
        if 'imx519' not in self.camera_info['device_info'].lower():
            print("\nWarning: This doesn't appear to be an IMX519 camera module.")
            print("The software is tested with IMX519 and may not work correctly with other cameras.")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return False

        # Step 3: Test camera capture
        print("\n3. Testing camera capture...")
        try:
            self.picam = Picamera2()

            # Test different configurations
            configs = [
                ("1080p", (1920, 1080)),
                ("720p", (1280, 720))
            ]

            results = []
            for name, resolution in configs:
                print(f"\nTesting {name} recording...")
                success = self._test_recording(resolution)
                results.append({
                    'resolution': name,
                    'success': success
                })

            # Save test results
            self.camera_info['test_results'] = results
            self._save_test_report()

            # Check if any tests failed
            if not all(r['success'] for r in results):
                print("\nWarning: Some tests failed. Check the test report for details.")
                return False

            print("\nCamera test completed successfully!")
            print(f"Test report saved to: {self.test_dir}/camera_test_report.json")
            return True

        except Exception as e:
            logging.error(f"Error during camera test: {e}")
            return False
        finally:
            if self.picam:
                self.picam.close()

    def _test_recording(self, resolution, duration=5):
        """Test recording at specific resolution"""
        try:
            # Configure camera
            video_config = self.picam.create_video_configuration(
                main={"size": resolution},
                controls={"FrameRate": 30}
            )
            self.picam.configure(video_config)

            # Start camera
            self.picam.start()

            # Create test recording
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_file = self.test_dir / f"test_{resolution[0]}x{resolution[1]}_{timestamp}.h264"

            encoder = H264Encoder(bitrate=10000000)
            output = FileOutput(str(test_file))

            print("Recording test clip...")
            self.picam.start_recording(encoder, output)
            time.sleep(duration)
            self.picam.stop_recording()

            # Convert to MP4
            mp4_file = test_file.with_suffix('.mp4')
            subprocess.run([
                'ffmpeg',
                '-i', str(test_file),
                '-c:v', 'copy',
                '-y',
                str(mp4_file)
            ], check=True)

            # Clean up h264 file
            test_file.unlink()

            print(f"Test recording saved: {mp4_file}")
            return True

        except Exception as e:
            logging.error(f"Error testing {resolution} recording: {e}")
            return False

    def _save_test_report(self):
        """Save test results to JSON file"""
        report_file = self.test_dir / 'camera_test_report.json'
        try:
            with open(report_file, 'w') as f:
                json.dump(self.camera_info, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving test report: {e}")


def main():
    print("\nSticky Sonic Camera Test Utility")
    print("==============================")

    tester = CameraTest()
    if tester.test_camera():
        print("\nCamera test completed successfully!")
        sys.exit(0)
    else:
        print("\nCamera test failed. Please check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()