#!/usr/bin/env python3
import json
import os
import threading
import logging
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import time
import subprocess
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

# Configure logging
logging.basicConfig(
    filename='field_recording.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class AudioRecorder:
    def __init__(self, device_id: int, sample_rate: int = 44100):
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.device = None
        self.recording = None

    def __enter__(self):
        """Setup audio device"""
        try:
            device_info = sd.query_devices(self.device_id, 'input')
            self.channels = device_info['max_input_channels']
            if self.channels <= 0:
                raise ValueError(f"Device {self.device_id} has no input channels")
            return self
        except Exception as e:
            logging.error(f"Error setting up audio device {self.device_id}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup audio device"""
        if self.recording is not None:
            try:
                sd.stop()
            except Exception as e:
                logging.error(f"Error stopping audio device {self.device_id}: {e}")

    def record(self, duration: int) -> None:
        """Record audio for specified duration"""
        try:
            self.recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device_id
            )
            sd.wait()
            return self.recording
        except Exception as e:
            logging.error(f"Error recording audio: {e}")
            return None


class VideoRecorder:
    def __init__(self, resolution=(1920, 1080), framerate=30):
        self.resolution = resolution
        self.framerate = framerate
        self.picam = None
        self.encoder = None
        self.output = None

    def __enter__(self):
        """Setup video recording device"""
        try:
            self.picam = Picamera2()
            video_config = self.picam.create_video_configuration(
                main={"size": self.resolution},
                controls={"FrameRate": self.framerate}
            )
            self.picam.configure(video_config)

            # High bitrate for better quality
            self.encoder = H264Encoder(bitrate=10000000)  # 10Mbps

            return self
        except Exception as e:
            logging.error(f"Error setting up camera: {e}")
            if self.picam:
                self.picam.close()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup video recording resources"""
        try:
            if self.picam:
                if self.picam.recording:
                    self.picam.stop_recording()
                self.picam.close()
                logging.info("Camera cleaned up successfully")
        except Exception as e:
            logging.error(f"Error cleaning up camera: {e}")

    def record(self, output_file: str, duration: int) -> bool:
        """Record video for specified duration"""
        try:
            self.output = FileOutput(output_file)

            # Start camera
            self.picam.start()

            # Start recording
            logging.info(f"Starting video recording to {output_file}")
            self.picam.start_recording(self.encoder, self.output)

            time.sleep(duration)

            self.picam.stop_recording()
            logging.info("Video recording completed successfully")
            return True

        except Exception as e:
            logging.error(f"Error during video recording: {e}")
            return False

    def convert_to_mp4(self, input_file: str, output_file: str) -> bool:
        """Convert h264 to mp4 format"""
        try:
            subprocess.run([
                'ffmpeg',
                '-i', input_file,
                '-c:v', 'copy',
                '-y',
                output_file
            ], check=True)

            os.remove(input_file)  # Remove original h264 file
            logging.info(f"Video conversion successful: {output_file}")
            return True

        except Exception as e:
            logging.error(f"Error converting video: {e}")
            return False


class AudioRecordingSession:
    def __init__(self, duration: int = 15, project_name: str = "sticky_sonic"):
        self.duration = duration
        self.project_name = project_name
        self.base_directory = "/home/pi/stickysonic/recordings"
        os.makedirs(self.base_directory, exist_ok=True)

        # Load mic configuration
        try:
            with open('/home/pi/stickysonic/mic_config.json', 'r') as f:
                self.mic_config = json.load(f)
        except FileNotFoundError:
            self.mic_config = []
            logging.warning("No microphone configuration found")

    def get_usb_device_ids(self):
        """Get configured USB audio devices"""
        devices = sd.query_devices()
        active_mics = []

        # Check which configured mics are present
        for mic in self.mic_config:
            try:
                device = devices[mic['id']]
                if 'USB' in str(device) and device.get('max_input_channels', 0) > 0:
                    active_mics.append((mic['id'], mic['label']))
                    logging.info(f"Found {mic['label']} microphone")
            except (KeyError, IndexError):
                logging.warning(f"Configured microphone {mic['label']} not found")

        return active_mics

    def start_recording(self):
        """Start recording from all configured microphones"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        active_mics = self.get_usb_device_ids()

        if not active_mics:
            logging.error("No configured microphones found")
            return

        threads = []
        for device_id, label in active_mics:
            filename = f"{self.project_name}_{timestamp}_{label}.wav"
            filepath = os.path.join(self.base_directory, filename)

            thread = threading.Thread(
                target=self._record_audio,
                args=(filepath, device_id)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def _record_audio(self, file_name: str, device_id: int) -> None:
        """Record audio with proper resource management"""
        with AudioRecorder(device_id) as recorder:
            recording = recorder.record(self.duration)
            if recording is not None:
                sf.write(file_name, recording, recorder.sample_rate)

    def _record_video(self, h264_file: str, mp4_file: str) -> None:
        """Record video with proper resource management"""
        with VideoRecorder() as recorder:
            if recorder.record(h264_file, self.duration):
                recorder.convert_to_mp4(h264_file, mp4_file)


# Main execution
if __name__ == "__main__":
    try:
        session = RecordingSession(duration=15)  # 15 seconds recording
        session.start_recording()
    except Exception as e:
        logging.error(f"Recording session failed: {e}")