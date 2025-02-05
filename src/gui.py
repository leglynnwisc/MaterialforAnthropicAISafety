import os
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import subprocess
import socket
from datetime import datetime, timedelta
import sounddevice as sd
import logging
import json
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pi/stickysonic/logs/app.log'),
        logging.StreamHandler()
    ]
)


class StickySonicGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("StickySonic Recording Control")
        self.root.geometry("600x800")

        # Set base paths
        self.base_path = Path('/home/pi/stickysonic')
        self.recordings_path = self.base_path / 'recordings'
        self.logs_path = self.base_path / 'logs'

        # Create necessary directories
        self.recordings_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Initialize variables
        self.init_variables()

        # Create GUI
        self.create_gui()

        # Load configuration
        self.load_config()

        # Start device monitoring
        self.check_devices()
        self.update_next_recording_time()

    def init_variables(self):
        """Initialize GUI variables"""
        self.status_var = tk.StringVar(value="Ready")
        self.next_recording_var = tk.StringVar(value="Not scheduled")
        self.duration_var = tk.StringVar(value="15")
        self.interval_var = tk.StringVar(value="5 minutes")
        self.usb_status_var = tk.StringVar(value="No USB drive detected")
        self.current_usb = None

        # Recording intervals and durations
        self.intervals = [
            "5 minutes", "15 minutes", "30 minutes",
            "1 hour", "2 hours", "3 hours", "4 hours",
            "6 hours", "12 hours", "24 hours"
        ]

        self.durations = [
            "30 seconds", "1 minute", "2 minutes", "5 minutes",
            "10 minutes", "15 minutes", "30 minutes", "1 hour"
        ]

    def create_gui(self):
        """Create main GUI elements"""
        # Create main container with padding
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create GUI sections
        self._create_status_section()
        self._create_device_section()
        self._create_recording_section()
        self._create_schedule_section()
        self._create_backup_section()
        self._create_control_section()

    def _create_status_section(self):
        """Create status display section"""
        frame = ttk.LabelFrame(self.main_frame, text="System Status", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Status:").pack(side=tk.LEFT)
        ttk.Label(frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)

        ttk.Label(frame, text="Next Recording:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(frame, textvariable=self.next_recording_var).pack(side=tk.LEFT)

    def _create_device_section(self):
        """Create device monitoring section"""
        frame = ttk.LabelFrame(self.main_frame, text="Connected Devices", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        # Audio devices
        self.audio_devices_text = tk.Text(frame, height=3, wrap=tk.WORD)
        self.audio_devices_text.pack(fill=tk.X, pady=5)

        # Refresh button
        ttk.Button(frame, text="Refresh Devices",
                   command=self.check_devices).pack(anchor=tk.E)

    def check_devices(self):
        """Check connected audio and video devices"""
        try:
            # Check audio devices
            devices = sd.query_devices()
            self.audio_devices_text.delete(1.0, tk.END)

            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if input_devices:
                for device in input_devices:
                    self.audio_devices_text.insert(tk.END,
                                                   f"Audio Device: {device['name']}\n")
            else:
                self.audio_devices_text.insert(tk.END, "No audio input devices found\n")

            # Check camera
            camera_result = subprocess.run(['vcgencmd', 'get_camera'],
                                           capture_output=True, text=True)
            if 'detected=1' in camera_result.stdout:
                self.audio_devices_text.insert(tk.END, "Camera: Connected ✓\n")
            else:
                self.audio_devices_text.insert(tk.END, "Camera: Not detected ✗\n")

        except Exception as e:
            logging.error(f"Error checking devices: {e}")
            self.audio_devices_text.delete(1.0, tk.END)
            self.audio_devices_text.insert(tk.END, f"Error checking devices: {e}")

    def _create_recording_section(self):
        """Create recording settings section"""
        frame = ttk.LabelFrame(self.main_frame, text="Recording Settings", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        # Recording duration
        duration_frame = ttk.Frame(frame)
        duration_frame.pack(fill=tk.X, pady=5)

        ttk.Label(duration_frame, text="Recording Duration:").pack(side=tk.LEFT)
        duration_combo = ttk.Combobox(duration_frame,
                                      textvariable=self.duration_var,
                                      values=self.durations,
                                      width=15)
        duration_combo.pack(side=tk.LEFT, padx=5)

    def _create_schedule_section(self):
        """Create scheduling section"""
        frame = ttk.LabelFrame(self.main_frame, text="Schedule Settings", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        # Recording interval
        interval_frame = ttk.Frame(frame)
        interval_frame.pack(fill=tk.X, pady=5)

        ttk.Label(interval_frame, text="Recording Interval:").pack(side=tk.LEFT)
        interval_combo = ttk.Combobox(interval_frame,
                                      textvariable=self.interval_var,
                                      values=self.intervals,
                                      width=15)
        interval_combo.pack(side=tk.LEFT, padx=5)

    def _create_backup_section(self):
        """Create backup controls section"""
        frame = ttk.LabelFrame(self.main_frame, text="Backup Controls", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, textvariable=self.usb_status_var).pack(anchor=tk.W)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Check USB Drive",
                   command=self.check_usb_drive).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Backup Recordings",
                   command=self.backup_recordings).pack(side=tk.LEFT, padx=5)

    def _create_control_section(self):
        """Create main control buttons section"""
        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=10)

        ttk.Button(frame, text="Start Schedule",
                   command=self.start_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Stop Schedule",
                   command=self.stop_schedule).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Test Recording",
                   command=self.test_recording).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Save Settings",
                   command=self.save_settings).pack(side=tk.RIGHT, padx=5)

    def load_config(self):
        """Load configuration from file"""
        config_path = self.base_path / 'config.ini'
        try:
            if config_path.exists():
                config = configparser.ConfigParser()
                config.read(config_path)
                if 'settings' in config:
                    self.duration_var.set(config['settings'].get('duration', '15 minutes'))
                    self.interval_var.set(config['settings'].get('interval', '5 minutes'))
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            messagebox.showwarning("Warning", f"Failed to load config: {e}")

    def save_settings(self):
        """Save current settings to config file"""
        try:
            config = configparser.ConfigParser()
            config['settings'] = {
                'duration': self.duration_var.get(),
                'interval': self.interval_var.get()
            }

            config_path = self.base_path / 'config.ini'
            with open(config_path, 'w') as configfile:
                config.write(configfile)

            self.create_systemd_services()
            messagebox.showinfo("Success", "Settings saved successfully")

        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def create_systemd_services(self):
        """Create systemd service and timer units"""
        try:
            # Convert duration to seconds
            duration = self._parse_time_to_seconds(self.duration_var.get())

            # Create service unit
            service_content = f"""[Unit]
Description=StickySonic Recording Service
After=sound.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {self.base_path}/record.py {duration}
User=pi
Environment=PYTHONPATH={self.base_path}
StandardOutput=append:{self.logs_path}/recorder.log
StandardError=append:{self.logs_path}/recorder.log

[Install]
WantedBy=multi-user.target
"""
            # Create timer unit
            interval_minutes = self._parse_time_to_minutes(self.interval_var.get())
            timer_content = f"""[Unit]
Description=StickySonic Recording Timer

[Timer]
OnBootSec=1min
OnUnitActiveSec={interval_minutes}min
AccuracySec=1s
Persistent=true

[Install]
WantedBy=timers.target
"""
            # Write service files
            subprocess.run(['sudo', 'tee', '/etc/systemd/system/stickysonic.service'],
                           input=service_content.encode(), check=True)
            subprocess.run(['sudo', 'tee', '/etc/systemd/system/stickysonic.timer'],
                           input=timer_content.encode(), check=True)

            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)

        except Exception as e:
            logging.error(f"Error creating systemd services: {e}")
            raise Exception(f"Failed to create systemd services: {e}")

    def _parse_time_to_seconds(self, time_str):
        """Convert time string to seconds"""
        try:
            number = int(time_str.split()[0])
            unit = time_str.split()[1].lower()

            if 'hour' in unit:
                return number * 3600
            elif 'minute' in unit:
                return number * 60
            elif 'second' in unit:
                return number
            else:
                raise ValueError(f"Unknown time unit: {unit}")
        except Exception as e:
            logging.error(f"Error parsing time: {e}")
            raise

    def _parse_time_to_minutes(self, time_str):
        """Convert time string to minutes"""
        return self._parse_time_to_seconds(time_str) // 60

    def start_schedule(self):
        """Start the recording schedule"""
        try:
            subprocess.run(['sudo', 'systemctl', 'enable', 'stickysonic.timer'], check=True)
            subprocess.run(['sudo', 'systemctl', 'start', 'stickysonic.timer'], check=True)
            self.status_var.set("Running")
            self.update_next_recording_time()
            messagebox.showinfo("Success", "Recording schedule started")
        except Exception as e:
            logging.error(f"Error starting schedule: {e}")
            messagebox.showerror("Error", f"Failed to start schedule: {e}")

    def stop_schedule(self):
        """Stop the recording schedule"""
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'stickysonic.timer'], check=True)
            subprocess.run(['sudo', 'systemctl', 'disable', 'stickysonic.timer'], check=True)
            self.status_var.set("Stopped")
            self.next_recording_var.set("Not scheduled")
            messagebox.showinfo("Success", "Recording schedule stopped")
        except Exception as e:
            logging.error(f"Error stopping schedule: {e}")
            messagebox.showerror("Error", f"Failed to stop schedule: {e}")

    def test_recording(self):
        """Perform a test recording"""
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'stickysonic.service'], check=True)
            messagebox.showinfo("Success", "Test recording started")
        except Exception as e:
            logging.error(f"Error starting test recording: {e}")
            messagebox.showerror("Error", f"Test recording failed: {e}")

        def check_usb_drive(self):
            """Check for mounted USB drives"""
            try:
                result = subprocess.run(['lsblk', '-o', 'NAME,MOUNTPOINT,SIZE,FSTYPE', '-J'],
                                        capture_output=True, text=True)
                devices = json.loads(result.stdout)

                # Find USB drives
                usb_drives = []
                for device in devices['blockdevices']:
                    for part in device.get('children', []):
                        if part.get('mountpoint') and part.get('mountpoint', '').startswith('/media/pi'):
                            usb_drives.append({
                                'mountpoint': part['mountpoint'],
                                'size': part['size'],
                                'fstype': part.get('fstype', 'unknown')
                            })

                if usb_drives:
                    drive = usb_drives[0]  # Use first USB drive found
                    free_space = self.get_free_space(drive['mountpoint'])
                    self.usb_status_var.set(
                        f"USB Drive Found: {free_space:.1f}GB free of {drive['size']}"
                    )
                    self.current_usb = drive['mountpoint']
                    return True
                else:
                    self.usb_status_var.set("No USB drive detected")
                    self.current_usb = None
                    return False

            except Exception as e:
                logging.error(f"Error checking USB: {e}")
                self.usb_status_var.set(f"Error checking USB: {str(e)}")
                return False

    def get_free_space(self, path):
        """Get free space in GB"""
        stat = os.statvfs(path)
        return (stat.f_frsize * stat.f_bavail) / (1024 ** 3)

    def backup_recordings(self):
        """Backup recordings to USB drive"""
        if not self.current_usb or not self.check_usb_drive():
            messagebox.showerror("Error", "No USB drive detected")
            return

        try:
            # Create backup directory on USB
            backup_dir = Path(self.current_usb) / 'stickysonic_backup'
            backup_dir.mkdir(exist_ok=True)

            # Get list of recordings
            recordings = list(self.recordings_path.glob('*'))
            if not recordings:
                messagebox.showinfo("Info", "No recordings found to backup")
                return

            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Backup Progress")
            progress_window.geometry("300x150")

            progress_var = tk.DoubleVar()
            progress_label = ttk.Label(progress_window, text="Starting backup...")
            progress_label.pack(pady=10)

            progress_bar = ttk.Progressbar(
                progress_window,
                variable=progress_var,
                maximum=100,
                length=200
            )
            progress_bar.pack(pady=10)

            # Calculate total size
            total_size = sum(f.stat().st_size for f in recordings)
            copied_size = 0

            # Perform backup
            for src_file in recordings:
                dst_file = backup_dir / src_file.name

                # Skip if file exists and sizes match
                if dst_file.exists() and dst_file.stat().st_size == src_file.stat().st_size:
                    copied_size += src_file.stat().st_size
                    continue

                # Copy file
                shutil.copy2(src_file, dst_file)
                copied_size += src_file.stat().st_size

                # Update progress
                progress = (copied_size / total_size) * 100
                progress_var.set(progress)
                progress_label.config(
                    text=f"Copying: {src_file.name}\n{progress:.1f}% complete"
                )
                progress_window.update()

            # Create backup manifest
            manifest_path = backup_dir / 'backup_manifest.txt'
            with open(manifest_path, 'w') as f:
                f.write(f"Backup created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Files backed up: {len(recordings)}\n")
                f.write(f"Total size: {total_size / (1024 * 1024):.1f} MB\n")
                f.write("\nFiles:\n")
                for file in recordings:
                    f.write(f"- {file.name}\n")

            progress_window.destroy()
            messagebox.showinfo(
                "Backup Complete",
                f"Successfully backed up {len(recordings)} files\nLocation: {backup_dir}"
            )

        except Exception as e:
            logging.error(f"Backup error: {e}")
            messagebox.showerror("Backup Error", str(e))

    def update_next_recording_time(self):
        """Update the next recording time display"""
        try:
            if self.status_var.get() == "Running":
                result = subprocess.run(
                    ['systemctl', 'status', 'stickysonic.timer'],
                    capture_output=True, text=True
                )

                for line in result.stdout.split('\n'):
                    if "Trigger:" in line:
                        next_time = line.split("Trigger:")[1].strip()
                        self.next_recording_var.set(next_time)
                        break
                else:
                    interval_minutes = self._parse_time_to_minutes(self.interval_var.get())
                    next_time = datetime.now() + timedelta(minutes=interval_minutes)
                    self.next_recording_var.set(next_time.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                self.next_recording_var.set("Not scheduled")

        except Exception as e:
            logging.error(f"Error updating next recording time: {e}")
            self.next_recording_var.set("Status unavailable")

        # Schedule next update in 60 seconds if running
        if self.status_var.get() == "Running":
            self.root.after(60000, self.update_next_recording_time)

if __name__ == "__main__":
    try:
        # Set up logging directory
        log_dir = Path('/home/pi/stickysonic/logs')
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'app.log'),
                logging.StreamHandler()
            ]
        )

        # Start application
        root = tk.Tk()
        app = StickySonicGUI(root)
        root.mainloop()

    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        messagebox.showerror("Critical Error",
                             f"Application failed to start: {e}\nCheck logs for details.")

