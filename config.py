import os

# OBS WebSocket 配置
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "your_password_here"  # 替换为你的密码

# 录制配置
RECORDING_FPS = 60
MOUSE_BOUNDARY_THRESHOLD = 10  # 鼠标边界阈值（像素）

# 路径配置（使用相对路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 当前脚本所在目录
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")  # 录像文件目录
LOGS_DIR = os.path.join(BASE_DIR, "action_logs")  # 动作日志目录

# 确保目录存在
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# 文件命名格式
RECORDING_NAME_FORMAT = "game_recording_%Y-%m-%d_%H-%M-%S.mp4"
LOG_NAME_FORMAT = "game_recording_%Y-%m-%d_%H-%M-%S_log.jsonl"

# 调试配置
DEBUG = True  # 是否打印调试信息
PRINT_INTERVAL = 100  # 每多少帧打印一次信息 