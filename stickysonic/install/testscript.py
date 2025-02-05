import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class SystemdTest:
    def __init__(self):
        self.recording_duration = 60  # 1 minute recordings
        self.interval = 5  # 5 minute interval
        self.test_periods = {
            '5m': {'minutes': 5, 'desc': '5 minutes'},
            '15m': {'minutes': 15, 'desc': '15 minutes'},
            '30m': {'minutes': 30, 'desc': '30 minutes'},
            '1': {'hours': 1, 'desc': '1 hour'},
            '2': {'hours': 2, 'desc': '2 hours'},
            '3': {'hours': 3, 'desc': '3 hours'},
            '4': {'hours': 4, 'desc': '4 hours'},
            '6': {'hours': 6, 'desc': '6 hours'},
            '9': {'hours': 9, 'desc': '9 hours'},
            '12': {'hours': 12, 'desc': '12 hours'},
            '24': {'hours': 24, 'desc': '24 hours'},
            'i': {'hours': None, 'desc': 'Indefinitely'}
        }

    def show_menu(self):
        """Display test duration menu"""
        print("\nSTICKY SONIC RECORDING SCHEDULE")
        print("=============================")
        print("\nRecording will run for 1 minute every 5 minutes.")
        print("Choose schedule duration:")
        print("------------------------")

        # Print minute-based options first
        print("\nShort Durations:")
        for key in ['5m', '15m', '30m']:
            print(f"{key}) {self.test_periods[key]['desc']}")

        # Print hour-based options
        print("\nLonger Durations:")
        for key in ['1', '2', '3', '4', '6', '9', '12', '24', 'i']:
            print(f"{key}) {self.test_periods[key]['desc']}")

        choice = input("\nEnter choice: ").lower()

        if choice not in self.test_periods:
            raise ValueError("Invalid duration selected")

        return choice

    def create_systemd_units(self):
        """Create systemd service and timer units"""
        service_content = f"""[Unit]
Description=Sticky Sonic Test Recording Service
After=sound.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/pi/stickysonic/record_audio_and_video.py {self.recording_duration}
User=pi
Environment=PYTHONPATH=/home/pi/stickysonic
StandardOutput=append:/home/pi/stickysonic/logs/test_recorder.log
StandardError=append:/home/pi/stickysonic/logs/test_recorder.log

[Install]
WantedBy=multi-user.target"""

        timer_content = f"""[Unit]
Description=Sticky Sonic Test Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec={self.interval}min
AccuracySec=1s
Persistent=true

[Install]
WantedBy=timers.target"""

        try:
            # Create logs directory
            os.makedirs('/home/pi/stickysonic/logs', exist_ok=True)

            # Write service file
            subprocess.run([
                'sudo', 'tee',
                '/etc/systemd/system/sticky-sonic-test.service'
            ], input=service_content.encode(), check=True)

            # Write timer file
            subprocess.run([
                'sudo', 'tee',
                '/etc/systemd/system/sticky-sonic-test.timer'
            ], input=timer_content.encode(), check=True)

            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)

        except Exception as e:
            raise Exception(f"Failed to create systemd units: {str(e)}")

    def calculate_expected_recordings(self, duration_key):
        """Calculate expected number of recordings for given duration"""
        duration = self.test_periods[duration_key]
        if duration.get('hours') is not None:
            total_minutes = duration['hours'] * 60
        elif duration.get('minutes') is not None:
            total_minutes = duration['minutes']
        else:
            return "Indefinite"

        return (total_minutes // self.interval)

    def run_test(self):
        """Run 30-minute system test"""
        try:
            print("\nRunning 30-minute System Test")
            print("============================")
            print("Recording 1 minute every 5 minutes")
            print("Expected recordings: 6")

            # Create and start systemd units
            self.create_systemd_units()
            subprocess.run(['sudo', 'systemctl', 'start', 'sticky-sonic-test.timer'], check=True)

            start_time = datetime.now()
            end_time = start_time + timedelta(minutes=30)
            recordings_completed = 0

            print(f"\nTest Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Will End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

            try:
                while datetime.now() < end_time:
                    now = datetime.now()
                    time_remaining = end_time - now

                    # Get next recording time
                    timer_status = subprocess.run(
                        ['systemctl', 'status', 'sticky-sonic-test.timer'],
                        capture_output=True, text=True
                    ).stdout

                    next_trigger = None
                    for line in timer_status.split('\n'):
                        if "Trigger:" in line:
                            next_trigger = line.split("Trigger:")[1].strip()
                            break

                    # Clear line and show status
                    sys.stdout.write('\r' + ' ' * 80 + '\r')
                    if next_trigger:
                        sys.stdout.write(
                            f"Next recording: {next_trigger} | "
                            f"Time remaining: {str(time_remaining).split('.')[0]} | "
                            f"Recordings completed: {recordings_completed}/6"
                        )
                    sys.stdout.flush()

                    # Check log for completed recordings
                    try:
                        with open('/home/pi/stickysonic/logs/test_recorder.log', 'r') as f:
                            recordings_completed = sum(1 for line in f if "Recording completed" in line)
                    except FileNotFoundError:
                        pass

                    time.sleep(1)

            except KeyboardInterrupt:
                print("\n\nTest interrupted by user.")

            # Stop and cleanup
            print("\nStopping test...")
            subprocess.run(['sudo', 'systemctl', 'stop', 'sticky-sonic-test.timer'], check=True)
            subprocess.run(['sudo', 'systemctl', 'stop', 'sticky-sonic-test.service'], check=True)

            # Show summary
            print("\nTest Summary")
            print("============")
            print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Recordings completed: {recordings_completed}/6")
            print("\nRecordings are saved in: /home/pi/stickysonic/recordings/")

        except Exception as e:
            print(f"\nError during test: {str(e)}")
            logging.error(f"Test failed: {e}")
            # Ensure timer is stopped on error
            subprocess.run(['sudo', 'systemctl', 'stop', 'sticky-sonic-test.timer'], check=True)
            raise


if __name__ == "__main__":
    try:
        test = SystemdTest()
        if len(sys.argv) > 1 and sys.argv[1] == '--test':
            test.run_test()  # Run 30-minute test
        else:
            duration = test.show_menu()  # Show full menu for normal operation
            test.run_schedules(duration)
    except KeyboardInterrupt:
        print("\nCancelled by user")
    except Exception as e:
        print(f"\nFailed: {str(e)}")
        logging.error(f"Failed: {e}")