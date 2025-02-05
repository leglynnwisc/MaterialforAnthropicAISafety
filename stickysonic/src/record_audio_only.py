#!/usr/bin/env python3

import os
import threading
import logging
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import time

# Configure logging
logging.basicConfig(
    filename='audio_recording.log',
    level=logging.INFO,
    format='%(asctime)s - rec%(levelname)s - %(message)s'
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


class RecordingSession:
    def __init__(self, duration: int = 15, project_name: str = "sticky_sonic"):
        self.duration = duration
        self.project_name = project_name
        self.base_directory = os.path.join(os.getcwd(), "recordings")
        os.makedirs(self.base_directory, exist_ok=True)

    def get_usb_device_ids(self):
        """Get IDs of connected USB audio devices"""
        devices = sd.query_devices()
        usb_devices = []
        for i, device in enumerate(devices):
            try:
                if 'USB' in device['name'] and device['max_input_channels'] > 0:
                    logging.info(f"Found USB device: {device['name']}")
                    usb_devices.append((i, device['name']))
            except KeyError as e:
                logging.error(f"Key error: {e} for device {i}: {device}")

        if not usb_devices:
            logging.warning("No USB audio devices found!")

        return usb_devices

    def start_recording(self) -> None:
        """Start a recording session"""
        try:
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_prefix = os.path.join(self.base_directory, f"{self.project_name}_{timestamp}")

            # Get USB audio devices
            usb_devices = self.get_usb_device_ids()
            if not usb_devices:
                raise ValueError("No audio devices available for recording")

            logging.info(f"Starting recording with devices: {usb_devices}")

            # Start recording threads
            threads = []

            # Audio recording threads
            for device_id, device_name in usb_devices:
                safe_device_name = device_name.replace(' ', '_').replace('/', '_')
                audio_file = f"{filename_prefix}_{safe_device_name}_{device_id}.wav"

                thread = threading.Thread(
                    target=self._record_audio,
                    args=(audio_file, device_id)
                )
                threads.append(thread)
                thread.start()
                logging.info(f"Started recording thread for device: {device_name}")

            # Wait for completion
            for thread in threads:
                thread.join()

            logging.info("Recording session completed successfully")

        except Exception as e:
            logging.error(f"Recording session failed: {e}")
            raise

    def _record_audio(self, file_name: str, device_id: int) -> None:
        """Record audio with proper resource management"""
        try:
            with AudioRecorder(device_id) as recorder:
                recording = recorder.record(self.duration)
                if recording is not None:
                    sf.write(file_name, recording, recorder.sample_rate)
                    logging.info(f"Successfully saved recording to {file_name}")
                else:
                    logging.error(f"Failed to record from device {device_id}")
        except Exception as e:
            logging.error(f"Error in _record_audio for device {device_id}: {e}")


if __name__ == "__main__":
    import sys

    try:
        duration = int(sys.argv[1]) if len(sys.argv) > 1 else 15
        session = AudioRecordingSession(duration=duration)
        session.start_recording()
    except Exception as e:
        logging.error(f"Recording session failed: {e}")