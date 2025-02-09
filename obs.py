from obswebsocket import obsws
import obsws_python as obs
import time
import os
import datetime
import threading

# 直接定义需要的函数，而不是从 main 导入
def start_input_recording():
    """Start recording keyboard and mouse inputs"""
    global recording
    recording = True

def save_log(video_filename=None):
    """Save the current log data"""
    # 实现日志保存逻辑
    pass

class OBSRecorder:
    def __init__(self, host, port, password, scene, recordings_dir, logs_dir, 
                 mouse_boundary_threshold=10, debug=True, print_interval=100, fps=60):
        self.host = host
        self.port = port
        self.password = password
        self.scene = scene
        self.recordings_dir = recordings_dir
        self.logs_dir = logs_dir
        self.mouse_boundary_threshold = mouse_boundary_threshold
        self.debug = debug
        self.print_interval = print_interval
        self.fps = fps
        
        self.client = None
        self.recording = False
        self.log_save_thread = None
        
        # 确保目录存在
        os.makedirs(recordings_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        
        # 初始化输入记录器
        from main import (record_mouse_events, 
                        record_mouse_position,
                        start_recording as start_input_tracking)
        
        # 启动鼠标事件记录线程
        self.mouse_events_thread = threading.Thread(target=record_mouse_events)
        self.mouse_events_thread.daemon = True
        self.mouse_events_thread.start()
        
        # 启动鼠标位置记录线程，传入所有配置参数
        self.mouse_position_thread = threading.Thread(
            target=lambda: record_mouse_position(
                self.mouse_boundary_threshold,
                self.fps,
                self.debug,
                self.print_interval
            )
        )
        self.mouse_position_thread.daemon = True
        self.mouse_position_thread.start()

    def connect(self):
        """Connect to OBS WebSocket"""
        try:
            self.client = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password
            )
            
            # 只在有场景名称时尝试设置场景
            if self.scene:
                try:
                    self.client.set_current_program_scene(self.scene)
                except Exception as e:
                    print(f"Warning: Failed to set scene: {e}")
                    # 继续执行，不中断连接
                
            print("Successfully connected to OBS")
            return True
            
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            return False
    
    def set_current_program_scene(self, scene_name):
        """设置当前场景"""
        if self.client and scene_name:
            self.client.set_current_program_scene(scene_name)
            self.scene = scene_name
    
    def _start_input_tracking(self):
        """Start tracking keyboard and mouse inputs"""
        start_input_recording()
    
    def start_recording(self):
        """Start recording in OBS"""
        if not self.client:
            if not self.connect():
                return None, None
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            recording_path = os.path.join(self.recordings_dir, f"game_recording_{timestamp}.mp4")
            
            os.makedirs(self.recordings_dir, exist_ok=True)
            
            try:
                self.client.set_record_directory(self.recordings_dir)
                self.client.start_record()
                self.recording = True
                
                # 启动所有输入记录
                from main import start_recording, save_log, record_mouse_events, record_mouse_position
                start_recording()  # 这里会初始化键盘监听
                
                # 第一次保存日志，创建新文件
                save_log(self.logs_dir, timestamp, self.debug)
                
                # 启动定期保存日志的线程
                def save_log_periodically():
                    while self.recording:
                        save_log(self.logs_dir, timestamp, self.debug)
                        time.sleep(10)
                
                self.log_save_thread = threading.Thread(target=save_log_periodically)
                self.log_save_thread.daemon = True
                self.log_save_thread.start()
                
                return recording_path, timestamp
                
            except Exception as e:
                print(f"Error starting OBS recording: {e}")
                return None, None
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            return None, None
    
    def stop_recording(self):
        """Stop recording in OBS"""
        if not self.client or not self.recording:
            return False
        
        try:
            # 停止 OBS 录制
            self.client.stop_record()
            self.recording = False
            
            # 等待日志保存线程结束
            if self.log_save_thread and self.log_save_thread.is_alive():
                self.log_save_thread.join(timeout=2)
            
            # 最后保存一次日志
            from main import save_log
            save_log(self.logs_dir)
            
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