from obswebsocket import obsws
import obsws_python.obsws_python as obs
import time
import os
import datetime
import threading
from main import (
    start_listener, 
    record_mouse_events,  # 新的鼠标事件记录函数
    record_mouse_position,  # 鼠标位置记录函数
    save_log, 
    start_recording as start_input_recording
)
import config

class OBSRecorder:
    def __init__(self, host="localhost", port=4455, password=None, output_path="recordings"):
        self.host = host
        self.port = port
        self.password = password
        self.output_path = output_path
        self.client = None
        self.recording = False
        
        # 确保录制目录存在
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(config.RECORDINGS_DIR, exist_ok=True)
        os.makedirs(config.LOGS_DIR, exist_ok=True)
    
    def connect(self):
        """Connect to OBS WebSocket"""
        try:
            self.client = obs.ReqClient(
                host=config.OBS_HOST,
                port=config.OBS_PORT,
                password=config.OBS_PASSWORD
            )
            print("Successfully connected to OBS")
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            return False
        return True
    
    def _start_input_tracking(self):
        """Start tracking keyboard and mouse inputs"""
        start_input_recording()
    
    def start_recording(self):
        """Start recording in OBS"""
        if not self.client:
            if not self.connect():
                return None, None
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime(config.RECORDING_NAME_FORMAT)
            recording_path = os.path.join(config.RECORDINGS_DIR, timestamp)
            
            # 确保录制文件的目录存在
            os.makedirs(os.path.dirname(recording_path), exist_ok=True)
            
            # Set up and start OBS recording
            try:
                self.client.start_record()
                self.recording = True
            except Exception as e:
                print(f"Error starting OBS recording: {e}")
                return None, None
            
            # Save first log entry with video filename to initialize the log file
            save_log(timestamp)
            
            # Start input tracking threads
            self._start_input_tracking()
            
            print(f"Started recording to {recording_path}")
            return recording_path, timestamp
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            return None, None
    
    def stop_recording(self):
        """Stop recording in OBS"""
        if not self.client or not self.recording:
            return False
        
        try:
            self.client.stop_record()
            self.recording = False
            print("Recording stopped")
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False

    def disconnect(self):
        """Disconnect from OBS"""
        if self.client:
            if self.recording:
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
        if recorder.connect():
            # Start recording
            full_path, video_filename = recorder.start_recording()
            if not full_path:
                return
            
            # Main recording loop
            try:
                while True:
                    time.sleep(10)  # Save log every 10 seconds
                    save_log()
                    
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