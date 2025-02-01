from obswebsocket import obsws
import obsws_python.obsws_python as obs
import time
import os
import pynput.keyboard
import datetime
import threading
from main import start_listener, start_mouse_listener, save_log, start_recording as start_input_recording

HOST = 0.0.0.0
PORT = 0
PASSWORD = "xxxxxxxxxxxxxxxx"

class OBSRecorder:
    def __init__(self, host=HOST, port=PORT, password=PASSWORD):
        self.host = host
        self.port = port
        self.password = password
        self.client = None
        self.recording_active = False
        self.output_path = r"recordings"

    def connect(self):
        """Connect to OBS WebSocket"""
        try:
            self.client = obs.ReqClient(host=self.host, port=self.port, password=self.password)
            print("Successfully connected to OBS")
        except Exception as e:
            raise Exception(f"Failed to connect to OBS: {e}")

    def start_recording(self):
        """Start recording and input tracking"""
        if not self.client:
            raise Exception("Not connected to OBS")

        try:
            # Check if recording is already active
            status = self.client.get_record_status()
            if status.output_active:
                print("Recording is already active")
                return None, None

            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"game_recording_{timestamp}.mp4"
            full_path = os.path.join(self.output_path, filename)
            
            # Set up and start OBS recording
            self.client.set_record_directory(self.output_path)
            self.client.set_current_program_scene("screen")
            self.client.start_record()
            self.recording_active = True

            # Initialize input recording timestamp
            start_input_recording()
            
            # Save first log entry with video filename to initialize the log file
            save_log(filename)

            # Start input tracking threads
            self._start_input_tracking()

            print(f"Started recording to {full_path}")
            return full_path, filename

        except Exception as e:
            self.recording_active = False
            raise Exception(f"Error starting recording: {e}")

    def stop_recording(self):
        """Stop recording and save final log"""
        if not self.client:
            return

        try:
            status = self.client.get_record_status()
            if not status.output_active:
                print("Recording is not active")
                return

            self.client.stop_record()
            self.recording_active = False
            save_log()  # Final save of the log
            print("Stopped recording")

        except Exception as e:
            print(f"Error stopping recording: {e}")
            raise

    def _start_input_tracking(self):
        """Start mouse and keyboard tracking threads"""
        # Start mouse tracking
        mouse_listener_thread = threading.Thread(target=start_mouse_listener)
        mouse_listener_thread.daemon = True
        mouse_listener_thread.start()

        # Start keyboard tracking
        listener_thread = threading.Thread(target=start_listener)
        listener_thread.daemon = True
        listener_thread.start()
        print("Started profiling mouse and keyboard movement")

    def disconnect(self):
        """Disconnect from OBS"""
        if self.client:
            if self.recording_active:
                try:
                    self.stop_recording()
                except:
                    pass
            self.client.disconnect()
            self.client = None

def main():
    recorder = OBSRecorder()
    
    try:
        # Connect to OBS
        recorder.connect()
        
        # Start recording
        full_path, video_filename = recorder.start_recording()
        if not full_path:
            return
        
        # Main recording loop
        try:
            interval = 10  # Save every 10 seconds
            while True:
                time.sleep(interval)
                save_log()  # Regular interval save
                
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
            
        finally:
            recorder.stop_recording()
            if video_filename:
                save_log(video_filename)  # Final save with video reference
                
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        recorder.disconnect()

if __name__ == '__main__':
    main()