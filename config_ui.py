import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
import time

# 添加一个全局配置类
class GlobalConfig:
    def __init__(self):
        # OBS WebSocket 配置
        self.OBS_HOST = "localhost"
        self.OBS_PORT = 4444
        self.OBS_PASSWORD = "1234567890"
        self.OBS_SCENE = ""
        
        # 录制配置
        self.RECORDING_FPS = 60
        self.MOUSE_BOUNDARY_THRESHOLD = 10
        
        # 初始化路径
        self.update_base_dir()
        
        # 文件命名格式
        self.RECORDING_NAME_FORMAT = "game_recording_%Y-%m-%d_%H-%M-%S.mp4"
        self.LOG_NAME_FORMAT = "game_recording_%Y-%m-%d_%H-%M-%S_log.jsonl"
        
        # 调试配置
        self.DEBUG = True
        self.PRINT_INTERVAL = 100

    def update_base_dir(self):
        """更新基础目录"""
        if getattr(sys, 'frozen', False):
            self.BASE_DIR = os.path.dirname(sys.executable)
            self.RECORDINGS_DIR = os.path.join(self.BASE_DIR, "recordings")
            self.LOGS_DIR = os.path.join(self.BASE_DIR, "action_logs")
        else:
            self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            self.RECORDINGS_DIR = os.path.join(self.BASE_DIR, "recordings")
            self.LOGS_DIR = os.path.join(self.BASE_DIR, "action_logs")
        

# 创建全局配置实例
global_config = GlobalConfig()

class ConfigUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Monitor Config")
        
        # 设置窗口大小和位置
        window_width = 600
        window_height = 500
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # OBS 配置
        ttk.Label(self.main_frame, text="OBS WebSocket 配置", 
                 font=('Helvetica', 12, 'bold')).grid(row=0, column=0, columnspan=3, pady=10)
        
        # Host
        ttk.Label(self.main_frame, text="Host:").grid(row=1, column=0, sticky=tk.W)
        self.host_var = tk.StringVar(value="localhost")
        ttk.Entry(self.main_frame, textvariable=self.host_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E))
        
        # Port
        ttk.Label(self.main_frame, text="Port:").grid(row=2, column=0, sticky=tk.W)
        self.port_var = tk.StringVar(value="4455")
        ttk.Entry(self.main_frame, textvariable=self.port_var).grid(
            row=2, column=1, sticky=(tk.W, tk.E))
        
        # Password
        ttk.Label(self.main_frame, text="Password:").grid(row=3, column=0, sticky=tk.W)
        self.password_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.password_var).grid(row=3, column=1, sticky=(tk.W, tk.E))
        
        # 添加测试连接按钮和场景选择
        ttk.Button(self.main_frame, text="测试连接",
                  command=self.test_connection).grid(row=3, column=2, padx=5)
        
        ttk.Label(self.main_frame, text="场景:").grid(row=4, column=0, sticky=tk.W)
        self.scene_var = tk.StringVar()
        self.scene_combo = ttk.Combobox(self.main_frame, textvariable=self.scene_var,
                                      state="readonly")
        self.scene_combo.grid(row=4, column=1, sticky=(tk.W, tk.E))
        
        # 录制配置
        ttk.Label(self.main_frame, text="录制配置", 
                 font=('Helvetica', 12, 'bold')).grid(row=5, column=0, columnspan=3, pady=10)
        
        # FPS
        ttk.Label(self.main_frame, text="FPS:").grid(row=6, column=0, sticky=tk.W)
        self.fps_var = tk.StringVar(value="60")
        fps_combo = ttk.Combobox(self.main_frame, textvariable=self.fps_var,
                                values=["30", "60"], state="readonly")
        fps_combo.grid(row=6, column=1, sticky=(tk.W, tk.E))
        
        # 鼠标边界阈值
        ttk.Label(self.main_frame, text="鼠标边界阈值:").grid(row=7, column=0, sticky=tk.W)
        self.threshold_var = tk.StringVar(value="10")
        ttk.Entry(self.main_frame, textvariable=self.threshold_var).grid(
            row=7, column=1, sticky=(tk.W, tk.E))
        
        # 路径配置
        ttk.Label(self.main_frame, text="路径配置", 
                 font=('Helvetica', 12, 'bold')).grid(row=8, column=0, columnspan=3, pady=10)
        
        # 录像目录
        ttk.Label(self.main_frame, text="录像目录:").grid(row=10, column=0, sticky=tk.W)
        self.recordings_var = tk.StringVar(value=global_config.RECORDINGS_DIR)
        self.recordings_entry = ttk.Entry(self.main_frame, textvariable=self.recordings_var)
        self.recordings_entry.grid(row=10, column=1, sticky=(tk.W, tk.E))
        self.recordings_button = ttk.Button(self.main_frame, text="浏览",
                                          command=lambda: self.browse_directory(self.recordings_var))
        self.recordings_button.grid(row=10, column=2)
        
        # 日志目录
        ttk.Label(self.main_frame, text="日志目录:").grid(row=11, column=0, sticky=tk.W)
        self.logs_var = tk.StringVar(value=global_config.LOGS_DIR)
        self.logs_entry = ttk.Entry(self.main_frame, textvariable=self.logs_var)
        self.logs_entry.grid(row=11, column=1, sticky=(tk.W, tk.E))
        self.logs_button = ttk.Button(self.main_frame, text="浏览",
                                     command=lambda: self.browse_directory(self.logs_var))
        self.logs_button.grid(row=11, column=2)
        
        # 调试配置
        ttk.Label(self.main_frame, text="调试配置", 
                 font=('Helvetica', 12, 'bold')).grid(row=12, column=0, columnspan=3, pady=10)
        
        # Debug模式
        ttk.Label(self.main_frame, text="Debug 模式:").grid(row=13, column=0, sticky=tk.W)
        self.debug_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.main_frame, text="启用",
                       variable=self.debug_var,
                       command=self.toggle_print_interval).grid(row=13, column=1, sticky=tk.W)
        
        # 打印间隔
        ttk.Label(self.main_frame, text="打印间隔(帧):").grid(row=14, column=0, sticky=tk.W)
        self.print_interval_var = tk.StringVar(value="100")
        self.print_entry = ttk.Entry(self.main_frame, textvariable=self.print_interval_var)
        self.print_entry.grid(row=14, column=1, sticky=(tk.W, tk.E))
        
        # 录制状态
        ttk.Label(self.main_frame, text="录制状态", 
                 font=('Helvetica', 12, 'bold')).grid(row=15, column=0, columnspan=3, pady=10)
        
        # 录制时长
        ttk.Label(self.main_frame, text="录制时长:").grid(row=16, column=0, sticky=tk.W)
        self.duration_var = tk.StringVar(value="00:00:00")
        ttk.Label(self.main_frame, textvariable=self.duration_var).grid(row=16, column=1, sticky=tk.W)
        
        # 输出路径
        ttk.Label(self.main_frame, text="当前输出:").grid(row=17, column=0, sticky=tk.W)
        self.output_path_var = tk.StringVar(value="未开始录制")
        ttk.Label(self.main_frame, textvariable=self.output_path_var).grid(row=17, column=1, sticky=tk.W)
        
        # 将开始录制按钮移到最下面
        self.recording_button = ttk.Button(self.main_frame, text="开始录制",
                                 command=self.start_recording)
        self.recording_button.grid(row=18, column=0, columnspan=3, pady=20)
        
        # 创建一个框架来容纳录制控制按钮
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.grid(row=18, column=0, columnspan=3, pady=20)
        
        # 在这个框架中放置开始录制按钮
        self.recording_button = ttk.Button(self.control_frame, text="开始录制",
                                 command=self.start_recording)
        self.recording_button.pack(side=tk.LEFT, padx=5)
        
        # 初始化状态
        self.toggle_print_interval()
        
        # 绑定变更事件
        self.bind_change_events()
        
        # 初始化 OBS 客户端
        self.obs_client = None
    
    def toggle_print_interval(self):
        """切换打印间隔输入框的状态"""
        state = "normal" if self.debug_var.get() else "disabled"
        self.print_entry.config(state=state)
    
    def browse_directory(self, var):
        """选择目录"""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)
            # 直接调用 save_config
            self.save_config()
            
            # 显示成功消息
            messagebox.showinfo("成功", "路径已更新！\n"
                              f"录像目录: {global_config.RECORDINGS_DIR}\n"
                              f"日志目录: {global_config.LOGS_DIR}")
    
    def test_connection(self):
        """测试 OBS 连接并获取场景列表"""
        try:
            import obsws_python as obs
            
            # 创建新的连接
            if self.obs_client:
                try:
                    self.obs_client.disconnect()
                except:
                    pass
            
            self.obs_client = obs.ReqClient(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                password=self.password_var.get()
            )
            
            # 获取场景列表
            scenes = self.obs_client.get_scene_list()
            scene_names = [scene['sceneName'] for scene in scenes.scenes]
            
            if len(scene_names) == 1:
                # 如果只有一个场景，直接设置并禁用选择
                self.scene_var.set(scene_names[0])
                self.scene_combo.config(state="disabled")
            else:
                # 多个场景时启用选择
                self.scene_combo['values'] = scene_names
                self.scene_combo.config(state="readonly")
                if scene_names:
                    self.scene_var.set(scene_names[0])
            
            # 立即保存配置
            self.save_config()
            messagebox.showinfo("成功", "成功连接到 OBS！")
            
        except Exception as e:
            messagebox.showerror("错误", f"连接失败: {str(e)}")
            self.obs_client = None
    
    def save_config(self):
        """保存配置到全局变量"""
        try:
            # 更新全局配置
            global_config.OBS_HOST = self.host_var.get()
            global_config.OBS_PORT = int(self.port_var.get())
            global_config.OBS_PASSWORD = self.password_var.get()
            global_config.OBS_SCENE = self.scene_var.get() or ""
            global_config.RECORDING_FPS = int(self.fps_var.get())
            global_config.MOUSE_BOUNDARY_THRESHOLD = int(self.threshold_var.get())
            
            # 处理路径
            recordings_dir = self.recordings_var.get().strip()
            logs_dir = self.logs_var.get().strip()
            
            global_config.DEBUG = self.debug_var.get()
            global_config.PRINT_INTERVAL = int(self.print_interval_var.get())
            
            # 检查目录是否合法
            if not os.path.exists(recordings_dir):
                try:
                    os.makedirs(recordings_dir)
                except:
                    messagebox.showerror("错误", f"录像目录无效或无法创建: {recordings_dir}")
                    return
                    
            if not os.access(recordings_dir, os.W_OK):
                messagebox.showerror("错误", f"录像目录没有写入权限: {recordings_dir}")
                return

            global_config.RECORDINGS_DIR = os.path.abspath(recordings_dir)

            if not os.path.exists(logs_dir):
                try:
                    os.makedirs(logs_dir)
                except:
                    messagebox.showerror("错误", f"日志目录无效或无法创建: {logs_dir}")
                    return
                
            if not os.access(logs_dir, os.W_OK):
                messagebox.showerror("错误", f"日志目录没有写入权限: {logs_dir}")
                return
            
            global_config.LOGS_DIR = os.path.abspath(logs_dir)
            
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
    def bind_change_events(self):
        """绑定变更事件"""
        for var in [self.host_var, self.port_var, self.password_var,
                   self.fps_var, self.threshold_var, self.recordings_var,
                   self.logs_var, self.debug_var, self.print_interval_var]:
            var.trace_add("write", lambda *args: self.save_config())
    
    def start_recording(self):
        """开始录制"""
        self.save_config()
        if not self.obs_client:
            if messagebox.askyesno("提示", "尚未连接到 OBS，是否现在连接？"):
                self.test_connection()
            else:
                return
        
        try:
            from obs import OBSRecorder
            recorder = OBSRecorder(
                host=self.host_var.get(),
                port=int(self.port_var.get()),
                password=self.password_var.get(),
                scene=self.scene_var.get(),
                recordings_dir=self.recordings_var.get(),
                logs_dir=self.logs_var.get(),
                mouse_boundary_threshold=int(self.threshold_var.get()),
                debug=self.debug_var.get(),
                print_interval=int(self.print_interval_var.get()),
                fps=int(self.fps_var.get())
            )
            
            # 连接到 OBS
            if not recorder.connect():
                messagebox.showerror("错误", "无法连接到 OBS")
                return
            
            # 设置场景（如果有选择场景的话）
            scene_name = self.scene_var.get()
            if scene_name:  # 只在有选择场景时设置
                try:
                    recorder.set_current_program_scene(scene_name)
                except Exception as e:
                    messagebox.showwarning("警告", f"设置场景失败: {str(e)}\n将使用当前场景继续录制")
            
            # 开始录制
            recording_path, timestamp = recorder.start_recording()
            if not recording_path:
                messagebox.showerror("错误", "开始录制失败")
                return
            
            # 更新界面显示
            self.output_path_var.set(recording_path)
            
            # 启动时长更新定时器
            self.start_time = time.time()
            self.recording_active = True
            self.update_duration()
            
            # 禁用开始录制按钮
            self.recording_button.config(state="disabled")
            
            # 添加停止录制按钮
            self.stop_button = ttk.Button(self.control_frame, text="停止录制",
                                        command=lambda: self.stop_recording(recorder))
            self.stop_button.pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")

    def update_duration(self):
        """更新录制时长显示"""
        if hasattr(self, 'start_time') and hasattr(self, 'recording_active'):
            if self.recording_active:
                duration = int(time.time() - self.start_time)
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60
                self.duration_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                self.root.after(1000, self.update_duration)

    def stop_recording(self, recorder):
        """停止录制"""
        try:
            recorder.stop_recording()
            recorder.disconnect()
            
            # 停止时间更新
            self.recording_active = False
            
            # 更新界面
            self.recording_button.config(state="normal")
            self.stop_button.destroy()
            
            # 显示录制完成信息
            duration = self.duration_var.get()
            output_path = self.output_path_var.get()
            messagebox.showinfo("录制完成", 
                              f"录制已完成\n时长: {duration}\n保存路径: {output_path}")
            
            # 重置显示
            self.duration_var.set("00:00:00")
            self.output_path_var.set("未开始录制")
            
        except Exception as e:
            messagebox.showerror("错误", f"停止录制失败: {str(e)}")

def main():
    root = tk.Tk()
    app = ConfigUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 