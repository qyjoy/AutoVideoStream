import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, Menu
import subprocess
import threading
import os
import glob
import time
import sys
import webbrowser

VIDEO_EXTENSIONS = ["*.webm", "*.mp4", "*.mkv", "*.mov", "*.avi", "*.flv"]
FFMPEG_DEFAULT_PATH = "ffmpeg"  # Assume ffmpeg is in PATH
DEFAULT_LANG = "zh_CN"
VERSION = '3.3 FE' # Version updated

# --- Main Application Class ---
class StreamerApp:
    def __init__(self, root):
        self.root = root
        self.setup_language()  # MUST be first
        self.root.title(self.get_translation('app_title'))
        self.root.geometry("450x500") # Adjusted width slightly for new button
        self.themes = {
            "默认 (Default)": {"bg": "#F0F0F0", "fg": "black", "widget_bg": "#FFFFFF", "widget_fg": "black",
                                "button_bg": "#E0E0E0", "button_fg": "black", "disabled_fg": "#A0A0A0",
                                "log_bg": "#FFFFFF", "log_fg": "black", "select_bg": "#0078D7", "select_fg": "white"},
            "夜间 (Night)": {"bg": "#2E2E2E", "fg": "white", "widget_bg": "#3C3C3C", "widget_fg": "white",
                              "button_bg": "#505050", "button_fg": "white", "disabled_fg": "#808080",
                              "log_bg": "#1E1E1E", "log_fg": "white", "select_bg": "#5A5A5A", "select_fg": "white"},
            "蓝调 (Blue)": {"bg": "#E3F2FD", "fg": "#0D47A1", "widget_bg": "#BBDEFB", "widget_fg": "#0D47A1",
                             "button_bg": "#90CAF9", "button_fg": "#0D47A1", "disabled_fg": "#64B5F6",
                             "log_bg": "#FFFFFF", "log_fg": "#1976D2", "select_bg": "#64B5F6", "select_fg": "white"},
            "炫彩 (Vibrant)": {"bg": "#FFF8E1", "fg": "#E65100", "widget_bg": "#FFECB3", "widget_fg": "#E65100",
                               "button_bg": "#FFB74D", "button_fg": "#BF360C", "disabled_fg": "#FFCC80",
                               "log_bg": "#FFFDE7", "log_fg": "#F57C00", "select_bg": "#FFA726", "select_fg": "black"},
            "绿色 (Green)": {"bg": "#E8F5E9", "fg": "#1B5E20", "widget_bg": "#C8E6C9", "widget_fg": "#1B5E20",
                              "button_bg": "#A5D6A7", "button_fg": "#1B5E20", "disabled_fg": "#81C784",
                              "log_bg": "#F1F8E9", "log_fg": "#388E3C", "select_bg": "#66BB6A", "select_fg": "white"},
            "粉色 (Pink)": {"bg": "#FCE4EC", "fg": "#880E4F", "widget_bg": "#F8BBD0", "widget_fg": "#880E4F",
                             "button_bg": "#F48FB1", "button_fg": "#880E4F", "disabled_fg": "#F06292",
                             "log_bg": "#FBE9E7", "log_fg": "#AD1457", "select_bg": "#EC407A", "select_fg": "white"}
        }
        self.selected_theme = tk.StringVar(value="默认 (Default)")

        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if 'clam' in available_themes:
            self.style.theme_use('clam')
        elif 'alt' in available_themes:
            self.style.theme_use('alt')

        self.rtmp_url = tk.StringVar()
        self.stream_key = tk.StringVar()
        self.video_folder = tk.StringVar()
        self.watermark_path = tk.StringVar()
        self.ffmpeg_path = tk.StringVar(value=FFMPEG_DEFAULT_PATH)
        self.add_watermark = tk.BooleanVar()
        self.video_encoder = tk.StringVar(value="libx264 (CPU)")
        self.audio_handling = tk.StringVar(value="aac (Re-encode)")

        self.streaming_active = False # Overall streaming state (controls loop)
        self.stop_requested = False   # Explicit stop requested by user
        self.switch_video_event = threading.Event() # Event to signal video switch
        self.stream_thread = None
        self.current_ffmpeg_process = None

        # --- GUI Setup ---
        self.create_menu()  # Creates menu structure
        self.create_widgets()  # Creates widgets, references are stored
        self.apply_theme()  # Apply default theme

    def setup_language(self):
        self.current_lang = tk.StringVar(value=DEFAULT_LANG)
        # --- Translations Dictionary ---
        self.translations = {
            "zh_CN": {
                "app_title": "AutoVideoStreamerGUI(自动循环推流)" + VERSION,
                "menu_theme": "主题 (Theme)",
                "lang_chinese": "简体中文",
                "lang_english": "English",
                "ffmpeg_path_label": "FFmpeg路径:",
                "browse_button": "浏览",
                "rtmp_url_label": "RTMP 推流地址:",
                "stream_key_label": "推流码 (Stream Key):",
                "video_folder_label": "视频文件夹:",
                "add_watermark_check": "添加水印",
                "video_encoder_label": "视频编码器:",
                "audio_handling_label": "音频处理:",
                "start_button": "开始推流",
                "stop_button": "停止推流",
                "switch_video_button": "切换视频",
                "log_output_label": "日志输出",
                "github_button": "Github发布页",
                "error_title": "错误",
                "info_title": "信息",
                "warn_title": "警告",
                "confirm_exit_title": "退出确认",
                "ffmpeg_not_found_msg": "未在路径 '{path}' 找到 ffmpeg.exe。请指定正确路径或确保其在系统 PATH 中。",
                "ffmpeg_execution_error_msg": "无法执行 FFmpeg ('{path}'). 请确保已安装并在 PATH 中，或指定正确的 .exe 文件路径。\n错误详情: {error}",
                "rtmp_url_invalid_msg": "RTMP 推流地址必须以 rtmp:// 开头且不能为空。",
                "stream_key_empty_msg": "推流码 (Stream Key) 不能为空。",
                "video_folder_invalid_msg": "请选择一个有效的视频文件夹。",
                "watermark_invalid_msg": "请选择一个有效的水印图片文件。",
                "stream_already_running_msg": "推流已经在运行中。",
                "stream_not_running_msg": "推流尚未开始。",
                "starting_stream_msg": "开始启动推流循环...",
                "stopping_stream_msg": "正在尝试停止推流...",
                "switching_video_msg": "正在请求切换到下一个视频...",
                "terminating_ffmpeg_msg": "正在终止当前的 FFmpeg 进程 (PID: {pid})...",
                "terminating_ffmpeg_for_switch_msg": "为切换视频，正在终止 FFmpeg 进程 (PID: {pid})...",
                "ffmpeg_terminated_msg": "FFmpeg 进程已正常终止。",
                "ffmpeg_terminate_failed_msg": "FFmpeg 进程未能正常终止，强制结束...",
                "ffmpeg_killed_msg": "FFmpeg 进程已被强制结束。",
                "ffmpeg_terminate_exception_msg": "无法终止 FFmpeg 进程: {error}",
                "stream_thread_still_active_warn": "推流线程在停止请求后仍然活跃。",
                "user_stop_completed_msg": "用户请求停止推流完成。",
                "user_switch_initiated_msg": "用户请求切换视频。",
                "no_videos_found_error": "在指定文件夹 '{folder}' 未找到视频文件 ({exts})。",
                "found_videos_msg": "找到 {count} 个视频文件。开始循环播放。",
                "loop_complete_msg": "完成一轮播放，从头开始下一轮。",
                "starting_file_msg": "--- 开始推流: {filename} ---",
                "copying_audio_info": "尝试直接复制音频流。如果源音频与目标不兼容可能会失败。",
                "executing_command_msg": "执行命令: {command}",
                "ffmpeg_output_log": "FFMPEG: {line}",
                "stop_detected_ffmpeg_output_msg": "在 FFmpeg 输出期间检测到停止请求。",
                "switch_detected_ffmpeg_output_msg": "在 FFmpeg 输出期间检测到切换视频请求。",
                "stop_detected_after_file_msg": "推流 {filename} 在结束后检测到停止信号。",
                "switch_detected_after_file_msg": "推流 {filename} 在结束后检测到切换信号，准备播放下一个。",
                "stream_finished_success_msg": "--- 完成推流: {filename} (成功) ---",
                "ffmpeg_error_exit_msg": "--- FFmpeg 错误退出 (代码 {code}) 对于: {filename} ---",
                "ffmpeg_error_context_msg": "FFmpeg 可能的错误信息:\n{context}",
                "continuing_after_error_warn": "检测到错误，将尝试播放列表中的下一个文件。",
                "ffmpeg_command_not_found_fatal": "FATAL ERROR: '{path}' 命令未找到。请检查 FFmpeg 路径设置。",
                "ffmpeg_unexpected_error_fatal": "FATAL ERROR: 运行 FFmpeg 时发生意外错误: {error}",
                "exiting_loop_after_file_msg": "在文件处理完成后退出推流循环。",
                "switching_to_next_video_msg": "--- 切换到下一个视频 ---",
                "loop_terminated_unexpectedly_warn": "WARN: 推流循环意外终止。",
                "buttons_reset_after_error_warn": "WARN: 推流循环已终止 (可能由于错误)。按钮已重置。",
                "stream_thread_finished_msg": "INFO: 推流线程结束。",
                "confirm_exit_msg": "推流正在进行中。\n您确定要停止推流并退出吗？",
                "nvenc_driver_warning": "WARN: 检测到 NVENC 编码器。请确保您的 NVIDIA 驱动版本 >= 570.0 以获得最佳兼容性，否则可能出错。",
                "amd_amf_warning": "WARN: 使用 h264_amf, 请确保驱动和 FFmpeg 支持良好。参数可能需调整。",
                "intel_qsv_warning": "WARN: 使用 h264_qsv, 请确保驱动和 FFmpeg 支持良好。参数可能需调整。",
                "ffmpeg_verified_msg": "INFO: 成功找到并验证 FFmpeg。",
                "search_video_error_msg": "ERROR: 搜索视频文件时出错: {error} (路径: {folder})",
                "filename_encoding_error": "[文件名编码错误 {index}]",
            },
            "en_US": {
                "app_title": "AutoVideoStreamerGUI" + VERSION,
                "menu_theme": "Theme",
                "lang_chinese": "简体中文",
                "lang_english": "English",
                "ffmpeg_path_label": "FFmpeg Path:",
                "browse_button": "Browse",
                "rtmp_url_label": "RTMP URL:",
                "stream_key_label": "Stream Key:",
                "video_folder_label": "Video Folder:",
                "add_watermark_check": "Add Watermark",
                "video_encoder_label": "Video Encoder:",
                "audio_handling_label": "Audio Handling:",
                "start_button": "Start Streaming",
                "stop_button": "Stop Streaming",
                "switch_video_button": "Switch Video",
                "log_output_label": "Log Output",
                "github_button": "Github",
                "error_title": "Error",
                "info_title": "Info",
                "warn_title": "Warning",
                "confirm_exit_title": "Confirm Exit",
                "ffmpeg_not_found_msg": "ffmpeg.exe not found at '{path}'. Please specify the correct path or ensure it's in the system PATH.",
                "ffmpeg_execution_error_msg": "Failed to execute FFmpeg ('{path}'). Ensure it's installed and in PATH, or specify the correct .exe path.\nError details: {error}",
                "rtmp_url_invalid_msg": "RTMP URL must start with rtmp:// and cannot be empty.",
                "stream_key_empty_msg": "Stream Key cannot be empty.",
                "video_folder_invalid_msg": "Please select a valid video folder.",
                "watermark_invalid_msg": "Please select a valid watermark image file.",
                "stream_already_running_msg": "Streaming is already in progress.",
                "stream_not_running_msg": "Streaming has not started yet.",
                "starting_stream_msg": "Starting stream loop...",
                "stopping_stream_msg": "Attempting to stop streaming...",
                "switching_video_msg": "Requesting switch to next video...",
                "terminating_ffmpeg_msg": "Terminating current FFmpeg process (PID: {pid})...",
                "terminating_ffmpeg_for_switch_msg": "Terminating FFmpeg process for video switch (PID: {pid})...",
                "ffmpeg_terminated_msg": "FFmpeg process terminated gracefully.",
                "ffmpeg_terminate_failed_msg": "FFmpeg process did not terminate gracefully, killing...",
                "ffmpeg_killed_msg": "FFmpeg process killed.",
                "ffmpeg_terminate_exception_msg": "Could not terminate FFmpeg process: {error}",
                "stream_thread_still_active_warn": "Stream thread still active after stop request.",
                "user_stop_completed_msg": "Streaming stop requested by user completed.",
                "user_switch_initiated_msg": "Video switch requested by user.",
                "no_videos_found_error": "ERROR: No video files found in the specified folder '{folder}' ({exts}).",
                "found_videos_msg": "INFO: Found {count} video files. Starting loop.",
                "loop_complete_msg": "INFO: Completed one cycle, starting next loop.",
                "starting_file_msg": "--- Starting stream for: {filename} ---",
                "copying_audio_info": "INFO: Attempting to copy audio stream. May fail if incompatible.",
                "executing_command_msg": "Executing: {command}",
                "ffmpeg_output_log": "FFMPEG: {line}",
                "stop_detected_ffmpeg_output_msg": "INFO: Stop requested detected during FFmpeg output.",
                "switch_detected_ffmpeg_output_msg": "INFO: Switch video request detected during FFmpeg output.",
                "stop_detected_after_file_msg": "INFO: Stop signal detected after processing {filename}.",
                "switch_detected_after_file_msg": "INFO: Switch signal detected after processing {filename}, preparing next video.",
                "stream_finished_success_msg": "--- Finished streaming: {filename} (Success) ---",
                "ffmpeg_error_exit_msg": "--- FFmpeg exited with error (code {code}) for: {filename} ---",
                "ffmpeg_error_context_msg": "FFmpeg potential error context:\n{context}",
                "continuing_after_error_warn": "WARN: Error detected, attempting next file in playlist.",
                "ffmpeg_command_not_found_fatal": "FATAL ERROR: '{path}' command not found. Check FFmpeg path setting.",
                "ffmpeg_unexpected_error_fatal": "FATAL ERROR: An unexpected error occurred running FFmpeg: {error}",
                "exiting_loop_after_file_msg": "INFO: Exiting stream loop after file completion due to stop request.",
                "switching_to_next_video_msg": "--- Switching to next video ---",
                "loop_terminated_unexpectedly_warn": "WARN: Stream loop terminated unexpectedly.",
                "buttons_reset_after_error_warn": "WARN: Stream loop terminated (possibly due to error). Buttons reset.",
                "stream_thread_finished_msg": "INFO: Stream thread finished.",
                "confirm_exit_msg": "Streaming is in progress.\nAre you sure you want to stop streaming and exit?",
                "nvenc_driver_warning": "WARN: NVENC encoder selected. Ensure your NVIDIA driver version is >= 570.0 for best compatibility, otherwise errors may occur.",
                "amd_amf_warning": "WARN: Using h264_amf, ensure drivers and FFmpeg support are correct. Parameters might need tuning.",
                "intel_qsv_warning": "WARN: Using h264_qsv, ensure drivers and FFmpeg support are correct. Parameters might need tuning.",
                "ffmpeg_verified_msg": "INFO: Found and verified FFmpeg successfully.",
                "search_video_error_msg": "ERROR: Error searching for video files: {error} (Path: {folder})",
                "filename_encoding_error": "[Filename Encoding Error {index}]",
            }
        }

    def get_translation(self, key, **kwargs):
        lang = self.current_lang.get()
        base_string = self.translations.get(lang, {}).get(key) or self.translations.get(DEFAULT_LANG, {}).get(key, f"<{key}>")
        try:
            return base_string.format(**kwargs)
        except Exception as e:
            print(f"Warning: Error formatting translation key '{key}': {e}")
            return f"<{key}> (Format Error)"

    def create_menu(self):
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)

        # 语言菜单（标题固定）
        self.lang_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="语言(Language)", menu=self.lang_menu)
        self.lang_menu.add_radiobutton(label=self.get_translation('lang_chinese'),
                                       variable=self.current_lang, value='zh_CN', command=self.switch_language)
        self.lang_menu.add_radiobutton(label=self.get_translation('lang_english'),
                                       variable=self.current_lang, value='en_US', command=self.switch_language)

        # 主题菜单（标题固定）
        self.theme_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="主题(Theme)", menu=self.theme_menu)
        for theme_name in self.themes:
            self.theme_menu.add_radiobutton(label=theme_name, variable=self.selected_theme, command=self.apply_theme)

    def switch_language(self):
        # 更新窗口标题和菜单项标签
        self.root.title(self.get_translation('app_title'))
        try:
            self.lang_menu.entryconfig(0, label=self.get_translation('lang_chinese'))
            self.lang_menu.entryconfig(1, label=self.get_translation('lang_english'))
        except Exception as e:
            print(f"语言菜单更新错误: {e}")

        # 更新所有可翻译控件的文本
        try:
            self.ffmpeg_label.config(text=self.get_translation('ffmpeg_path_label'))
            self.ffmpeg_browse_btn.config(text=self.get_translation('browse_button'))
            self.rtmp_label.config(text=self.get_translation('rtmp_url_label'))
            self.key_label.config(text=self.get_translation('stream_key_label'))
            self.folder_label.config(text=self.get_translation('video_folder_label'))
            self.folder_browse_btn.config(text=self.get_translation('browse_button'))
            self.watermark_check.config(text=self.get_translation('add_watermark_check'))
            self.watermark_browse_btn.config(text=self.get_translation('browse_button'))
            self.video_encoder_label.config(text=self.get_translation('video_encoder_label'))
            self.audio_handling_label.config(text=self.get_translation('audio_handling_label'))
            self.start_button.config(text=self.get_translation('start_button'))
            self.stop_button.config(text=self.get_translation('stop_button'))
            self.switch_video_button.config(text=self.get_translation('switch_video_button'))
            self.github_button.config(text=self.get_translation('github_button'))
            self.log_frame.config(text=self.get_translation('log_output_label'))
        except AttributeError as e:
            print(f"ERROR: Widget reference missing during language switch: {e}")

        self.apply_theme()

    def apply_theme(self):
        theme_name = self.selected_theme.get()
        theme = self.themes.get(theme_name, self.themes["默认 (Default)"])
        bg = theme["bg"]
        fg = theme["fg"]
        widget_bg = theme["widget_bg"]
        widget_fg = theme["widget_fg"]
        button_bg = theme["button_bg"]
        button_fg = theme["button_fg"]
        disabled_fg = theme["disabled_fg"]
        log_bg = theme["log_bg"]
        log_fg = theme["log_fg"]
        select_bg = theme["select_bg"]
        select_fg = theme["select_fg"]

        self.root.config(bg=bg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background=button_bg, foreground=button_fg, padding=5)
        self.style.map("TButton", background=[('active', select_bg), ('disabled', button_bg)],
                       foreground=[('active', select_fg), ('disabled', disabled_fg)])
        self.style.configure("TEntry", fieldbackground=widget_bg, foreground=widget_fg, insertcolor=widget_fg)
        self.style.map("TEntry", fieldbackground=[('disabled', bg)], foreground=[('disabled', disabled_fg)])
        self.style.configure("TCombobox", fieldbackground=widget_bg, foreground=widget_fg, background=button_bg, arrowcolor=fg)
        self.style.map("TCombobox", fieldbackground=[('readonly', widget_bg), ('disabled', bg)],
                       foreground=[('readonly', widget_fg), ('disabled', disabled_fg)],
                       selectbackground=[('readonly', select_bg)], selectforeground=[('readonly', select_fg)])
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.map("TCheckbutton", background=[('active', bg)], foreground=[('active', fg), ('disabled', disabled_fg)])
        self.style.configure("TLabelFrame", background=bg, foreground=fg, bordercolor=fg)
        self.style.configure("TLabelFrame.Label", background=bg, foreground=fg)

        # Re-apply styles to widgets that might not update automatically
        if hasattr(self, 'input_frame'):
            for widget in self.input_frame.winfo_children():
                if hasattr(widget, 'configure') and 'style' in widget.configure():
                     widget.configure(style=widget.winfo_class())
            for widget in self.control_frame.winfo_children():
                if hasattr(widget, 'configure') and 'style' in widget.configure():
                     widget.configure(style=widget.winfo_class())
            for widget in self.log_frame.winfo_children():
                 if isinstance(widget, (ttk.Frame, ttk.Label)):
                     if hasattr(widget, 'configure') and 'style' in widget.configure():
                         widget.configure(style=widget.winfo_class())

        if hasattr(self, 'log_area'):
            current_state = self.log_area['state']
            try:
                self.log_area.config(state=tk.NORMAL)
                self.log_area.config(bg=log_bg, fg=log_fg, selectbackground=select_bg,
                                     selectforeground=select_fg, insertbackground=fg)
            finally:
                self.log_area.config(state=current_state)

        # Ensure states are correct after theme change
        self.toggle_watermark_entry()
        self.update_control_states()


    def create_widgets(self):
        # --- Input Frame ---
        self.input_frame = ttk.Frame(self.root, padding="10")
        self.input_frame.pack(pady=0, padx=1, fill=tk.X)

        self.ffmpeg_label = ttk.Label(self.input_frame, text=self.get_translation('ffmpeg_path_label'))
        self.ffmpeg_label.grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.ffmpeg_entry = ttk.Entry(self.input_frame, textvariable=self.ffmpeg_path, width=50)
        self.ffmpeg_entry.grid(row=0, column=1, padx=5, pady=3, sticky=tk.EW)
        self.ffmpeg_browse_btn = ttk.Button(self.input_frame, text=self.get_translation('browse_button'),
                                            command=self.browse_ffmpeg)
        self.ffmpeg_browse_btn.grid(row=0, column=2, padx=5, pady=3)

        self.rtmp_label = ttk.Label(self.input_frame, text=self.get_translation('rtmp_url_label'))
        self.rtmp_label.grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.rtmp_entry = ttk.Entry(self.input_frame, textvariable=self.rtmp_url, width=60)
        self.rtmp_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=3, sticky=tk.EW)

        self.key_label = ttk.Label(self.input_frame, text=self.get_translation('stream_key_label'))
        self.key_label.grid(row=2, column=0, padx=5, pady=3, sticky=tk.W)
        self.key_entry = ttk.Entry(self.input_frame, textvariable=self.stream_key, width=60)
        self.key_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=3, sticky=tk.EW)

        self.folder_label = ttk.Label(self.input_frame, text=self.get_translation('video_folder_label'))
        self.folder_label.grid(row=3, column=0, padx=5, pady=3, sticky=tk.W)
        self.folder_entry = ttk.Entry(self.input_frame, textvariable=self.video_folder, width=50)
        self.folder_entry.grid(row=3, column=1, padx=5, pady=3, sticky=tk.EW)
        self.folder_browse_btn = ttk.Button(self.input_frame, text=self.get_translation('browse_button'),
                                            command=self.browse_folder)
        self.folder_browse_btn.grid(row=3, column=2, padx=5, pady=3)

        self.watermark_check = ttk.Checkbutton(self.input_frame, text=self.get_translation('add_watermark_check'),
                                               variable=self.add_watermark, command=self.toggle_watermark_entry)
        self.watermark_check.grid(row=4, column=0, padx=5, pady=3, sticky=tk.W)
        self.watermark_entry = ttk.Entry(self.input_frame, textvariable=self.watermark_path, width=50, state=tk.DISABLED)
        self.watermark_entry.grid(row=4, column=1, padx=5, pady=3, sticky=tk.EW)
        self.watermark_browse_btn = ttk.Button(self.input_frame, text=self.get_translation('browse_button'),
                                               command=self.browse_watermark, state=tk.DISABLED)
        self.watermark_browse_btn.grid(row=4, column=2, padx=5, pady=3)

        self.video_encoder_label = ttk.Label(self.input_frame, text=self.get_translation('video_encoder_label'))
        self.video_encoder_label.grid(row=5, column=0, padx=5, pady=3, sticky=tk.W)
        self.video_encoder_combo = ttk.Combobox(self.input_frame, textvariable=self.video_encoder,
                                                values=["libx264 (CPU)", "h264_nvenc (Nvidia)",
                                                        "h264_amf (AMD)", "h264_qsv (Intel)"],
                                                state="readonly")
        self.video_encoder_combo.grid(row=5, column=1, columnspan=2, padx=5, pady=1, sticky=tk.EW)

        self.audio_handling_label = ttk.Label(self.input_frame, text=self.get_translation('audio_handling_label'))
        self.audio_handling_label.grid(row=6, column=0, padx=5, pady=1, sticky=tk.W)
        self.audio_handling_combo = ttk.Combobox(self.input_frame, textvariable=self.audio_handling,
                                                 values=["aac (Re-encode)", "copy (Try Direct Copy)"],
                                                 state="readonly")
        self.audio_handling_combo.grid(row=6, column=1, columnspan=2, padx=5, pady=1, sticky=tk.EW)

        self.input_frame.columnconfigure(1, weight=1)

        # --- Control Frame ---
        self.control_frame = ttk.Frame(self.root, padding="10")
        self.control_frame.pack(pady=1, padx=1, fill=tk.X)

        self.start_button = ttk.Button(self.control_frame, text=self.get_translation('start_button'),
                                       command=self.start_streaming)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=1)
        self.stop_button = ttk.Button(self.control_frame, text=self.get_translation('stop_button'),
                                      command=self.stop_streaming, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=1)
        # New Switch Video Button
        self.switch_video_button = ttk.Button(self.control_frame, text=self.get_translation('switch_video_button'),
                                              command=self.switch_video, state=tk.DISABLED)
        self.switch_video_button.pack(side=tk.LEFT, padx=5, pady=1)
        self.github_button = ttk.Button(self.control_frame, text=self.get_translation('github_button'),
                                        command=lambda: webbrowser.open("https://github.com/qyjoy/AutoVideoStream"))
        self.github_button.pack(side=tk.LEFT, padx=5, pady=1)


        # --- Log Output Frame ---
        self.log_frame = ttk.LabelFrame(self.root, text=self.get_translation('log_output_label'), padding="10")
        self.log_frame.pack(pady=3, padx=5, fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED,
                                                  maxundo=100, undo=True, autoseparators=True, blockcursor=False)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        def _log_on_main_thread():
            # Avoid logging if root is already destroyed
            if not self.root or not self.root.winfo_exists():
                 print(f"Log suppressed (root destroyed): {message}")
                 return

            current_state = self.log_area['state']
            try:
                self.log_area.config(state=tk.NORMAL)
                log_entry = f"{time.strftime('%H:%M:%S')} - {message}\n"
                self.log_area.insert(tk.END, log_entry)
                # Maintain max 1000 log lines
                line_count = int(self.log_area.index('end-1c').split('.')[0])
                if line_count > 1000:
                    excess = line_count - 1000
                    self.log_area.delete("1.0", f"{excess + 1}.0 lineend")
                    # Limit undo history clearing frequency for performance
                    if excess % 100 == 0:
                        self.log_area.edit_reset()
                self.log_area.see(tk.END)
            except tk.TclError as e:
                 print(f"TclError during log update: {e}. Message: {message}") # Handle potential errors if GUI is closing
            finally:
                try:
                    # Only change state back if widget still exists
                    if self.log_area.winfo_exists():
                        self.log_area.config(state=current_state)
                except tk.TclError:
                    pass # Ignore if widget is destroyed
            print(message) # Also print to console

        # Use 'after' only if the root window still exists
        if self.root and self.root.winfo_exists():
            self.root.after(0, _log_on_main_thread)
        else:
             print(f"Log suppressed (root destroyed): {message}")


    def browse_ffmpeg(self):
        path = filedialog.askopenfilename(title="Select ffmpeg.exe", filetypes=[("Executable", "*.exe"), ("All Files", "*.*")])
        if path:
            self.ffmpeg_path.set(path)

    def browse_folder(self):
        path = filedialog.askdirectory(title=self.get_translation('video_folder_label'))
        if path:
            self.video_folder.set(path)

    def browse_watermark(self):
        path = filedialog.askopenfilename(title=self.get_translation('add_watermark_check'),
                                          filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.watermark_path.set(path)

    def toggle_watermark_entry(self):
        if not hasattr(self, 'watermark_entry') or not self.watermark_entry.winfo_exists(): # Check if widget exists
             return
        if self.add_watermark.get():
            self.watermark_entry.config(state=tk.NORMAL)
            self.watermark_browse_btn.config(state=tk.NORMAL)
        else:
            self.watermark_entry.config(state=tk.DISABLED)
            self.watermark_browse_btn.config(state=tk.DISABLED)
            self.watermark_path.set("")

    def update_control_states(self):
        # Ensure widgets exist before configuring
        if not hasattr(self, 'start_button') or not self.start_button.winfo_exists():
            return

        if self.streaming_active:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.switch_video_button.config(state=tk.NORMAL) # Enable switch button
            self.video_encoder_combo.config(state=tk.DISABLED)
            self.audio_handling_combo.config(state=tk.DISABLED)
            self.ffmpeg_entry.config(state=tk.DISABLED)
            self.ffmpeg_browse_btn.config(state=tk.DISABLED)
            self.rtmp_entry.config(state=tk.DISABLED)
            self.key_entry.config(state=tk.DISABLED)
            self.folder_entry.config(state=tk.DISABLED)
            self.folder_browse_btn.config(state=tk.DISABLED)
            self.watermark_check.config(state=tk.DISABLED)
            # Use toggle_watermark_entry to handle watermark state correctly
            self.toggle_watermark_entry()
            # Ensure watermark controls are disabled if add_watermark is false during streaming (shouldn't happen but safe)
            if not self.add_watermark.get():
                if hasattr(self, 'watermark_entry') and self.watermark_entry.winfo_exists(): self.watermark_entry.config(state=tk.DISABLED)
                if hasattr(self, 'watermark_browse_btn') and self.watermark_browse_btn.winfo_exists(): self.watermark_browse_btn.config(state=tk.DISABLED)

        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.switch_video_button.config(state=tk.DISABLED) # Disable switch button
            self.video_encoder_combo.config(state="readonly")
            self.audio_handling_combo.config(state="readonly")
            self.ffmpeg_entry.config(state=tk.NORMAL)
            self.ffmpeg_browse_btn.config(state=tk.NORMAL)
            self.rtmp_entry.config(state=tk.NORMAL)
            self.key_entry.config(state=tk.NORMAL)
            self.folder_entry.config(state=tk.NORMAL)
            self.folder_browse_btn.config(state=tk.NORMAL)
            self.watermark_check.config(state=tk.NORMAL)
            self.toggle_watermark_entry() # Make sure watermark entry state is correct

    def validate_inputs(self):
        ffmpeg_path_val = self.ffmpeg_path.get()
        if not os.path.exists(ffmpeg_path_val) and ffmpeg_path_val != FFMPEG_DEFAULT_PATH:
            messagebox.showerror(self.get_translation('error_title'),
                                 self.get_translation('ffmpeg_not_found_msg', path=ffmpeg_path_val))
            return False
        if ffmpeg_path_val == FFMPEG_DEFAULT_PATH or not os.path.exists(ffmpeg_path_val):
            # Check if ffmpeg is actually callable if using default path or path doesn't exist
            try:
                startupinfo = None
                creationflags = 0
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    creationflags = subprocess.CREATE_NO_WINDOW
                # Use the potentially modified ffmpeg_path_val (which might just be 'ffmpeg')
                subprocess.run([ffmpeg_path_val, "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               startupinfo=startupinfo, creationflags=creationflags)
                self.log(self.get_translation('ffmpeg_verified_msg'))
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                messagebox.showerror(self.get_translation('error_title'),
                                     self.get_translation('ffmpeg_execution_error_msg', path=ffmpeg_path_val, error=e))
                return False
            except Exception as e: # Catch broader exceptions during validation
                 messagebox.showerror(self.get_translation('error_title'),
                                     f"Unexpected error validating FFmpeg: {e}")
                 return False
        rtmp_url_val = self.rtmp_url.get().strip()
        stream_key_val = self.stream_key.get().strip()
        if not rtmp_url_val or not rtmp_url_val.lower().startswith("rtmp://"):
            messagebox.showerror(self.get_translation('error_title'), self.get_translation('rtmp_url_invalid_msg'))
            return False
        if not stream_key_val:
            messagebox.showerror(self.get_translation('error_title'), self.get_translation('stream_key_empty_msg'))
            return False
        video_folder_val = self.video_folder.get()
        if not video_folder_val or not os.path.isdir(video_folder_val):
            messagebox.showerror(self.get_translation('error_title'), self.get_translation('video_folder_invalid_msg'))
            return False
        if self.add_watermark.get():
            watermark_path_val = self.watermark_path.get()
            if not watermark_path_val or not os.path.isfile(watermark_path_val):
                messagebox.showerror(self.get_translation('error_title'), self.get_translation('watermark_invalid_msg'))
                return False
        return True

    def start_streaming(self):
        if not self.validate_inputs():
            return
        if self.streaming_active:
            self.log(self.get_translation('stream_already_running_msg'))
            return

        self.streaming_active = True
        self.stop_requested = False # Ensure stop flag is reset
        self.switch_video_event.clear() # Ensure switch event is reset
        self.update_control_states()
        self.log(self.get_translation('starting_stream_msg'))
        self.stream_thread = threading.Thread(target=self.stream_loop, daemon=True)
        self.stream_thread.start()

    def _request_ffmpeg_termination(self, reason="stop"):
        """Requests termination of the current ffmpeg process without waiting."""
        # Renamed from _terminate_ffmpeg_process to clarify it only sends signals
        process_to_terminate = self.current_ffmpeg_process # Capture current process locally
        if process_to_terminate and process_to_terminate.poll() is None:
            pid = process_to_terminate.pid
            log_msg_key = 'terminating_ffmpeg_for_switch_msg' if reason == "switch" else 'terminating_ffmpeg_msg'
            self.log(self.get_translation(log_msg_key, pid=pid))
            try:
                # Try graceful termination first
                process_to_terminate.terminate()
                # Start a separate thread to handle kill if terminate fails after timeout
                # This avoids blocking the UI thread or the stream_loop's signal handling
                threading.Thread(target=self._ensure_ffmpeg_killed, args=(process_to_terminate, pid), daemon=True).start()

            except Exception as e:
                # Log error if initial terminate call fails
                self.log(self.get_translation('ffmpeg_terminate_exception_msg', error=e))
        # DO NOT set self.current_ffmpeg_process = None here. Let the main loop handle it.

    def _ensure_ffmpeg_killed(self, process, expected_pid):
        """Waits briefly for terminate, then kills if necessary."""
        try:
            process.wait(timeout=2) # Wait for terminate to work
            self.log(self.get_translation('ffmpeg_terminated_msg') + f" (PID: {expected_pid})")
        except subprocess.TimeoutExpired:
            if process.poll() is None: # Check if it's still running
                self.log(self.get_translation('ffmpeg_terminate_failed_msg') + f" (PID: {expected_pid})")
                try:
                    process.kill()
                    process.wait(timeout=1) # Short wait after kill
                    self.log(self.get_translation('ffmpeg_killed_msg') + f" (PID: {expected_pid})")
                except Exception as kill_e:
                    self.log(f"Error killing FFmpeg process (PID: {expected_pid}): {kill_e}")
        except Exception as wait_e:
             self.log(f"Error waiting for FFmpeg process termination (PID: {expected_pid}): {wait_e}")


    def stop_streaming(self):
        if not self.streaming_active:
            self.log(self.get_translation('stream_not_running_msg'))
            return

        self.log(self.get_translation('stopping_stream_msg'))
        self.stop_requested = True      # Signal the loop to stop
        self.streaming_active = False   # Prevent new loops/videos
        self.switch_video_event.set() # Also set switch event to interrupt ffmpeg read quickly

        self._request_ffmpeg_termination(reason="stop") # Request termination

        # Schedule the UI update and final log message
        def _finalize_stop():
            # Wait briefly for thread to potentially finish processing the stop signal
            if self.stream_thread and self.stream_thread.is_alive():
                 self.stream_thread.join(timeout=1.0) # Slightly longer timeout for stop
                 if self.stream_thread.is_alive():
                     self.log(self.get_translation('stream_thread_still_active_warn'))
            # Ensure UI updates happen even if thread join times out
            if self.root and self.root.winfo_exists(): # Check root validity
                # Update states only if the stream is not marked as active anymore
                if not self.streaming_active:
                     self.update_control_states()
                self.log(self.get_translation('user_stop_completed_msg'))
            else:
                 print("Stop finalized after root destroyed.")

        if self.root and self.root.winfo_exists():
            # Use after_idle to ensure it runs after pending events, giving thread more time
            self.root.after_idle(_finalize_stop)
        else:
             print("Root destroyed before scheduling finalize_stop.")


    def switch_video(self):
        if not self.streaming_active:
            self.log(self.get_translation('stream_not_running_msg'))
            return

        self.log(self.get_translation('switching_video_msg'))
        self.switch_video_event.set() # Signal the loop to switch

        # Request termination of the *current* ffmpeg process
        self._request_ffmpeg_termination(reason="switch")

        self.log(self.get_translation('user_switch_initiated_msg'))


    def stream_loop(self):
        folder = self.video_folder.get()
        video_files = []
        try:
            safe_folder = folder
            # Attempt to handle potential encoding issues on Windows more robustly
            if os.name == 'nt':
                 try:
                      # Try decoding from filesystem encoding, re-encoding to UTF-8
                      safe_folder_bytes = safe_folder.encode(sys.getfilesystemencoding(), 'surrogateescape')
                      safe_folder = safe_folder_bytes.decode('utf-8', 'replace')
                 except Exception as enc_err:
                      self.log(f"WARN: Could not fully normalize folder path encoding: {folder}. Error: {enc_err}")
            for ext in VIDEO_EXTENSIONS:
                # Use os.path.join for cross-platform compatibility
                pattern = os.path.join(safe_folder, ext)
                video_files.extend(glob.iglob(pattern))
        except Exception as e:
            self.log(self.get_translation('search_video_error_msg', error=e, folder=folder))
            # Schedule UI reset from the main thread
            if self.root and self.root.winfo_exists():
                 self.root.after(100, self.reset_controls_after_error)
            return

        video_files = list(video_files) # Ensure it's a list
        if not video_files:
            self.log(self.get_translation('no_videos_found_error', folder=folder, exts=', '.join(VIDEO_EXTENSIONS)))
            if self.root and self.root.winfo_exists():
                self.root.after(100, self.reset_controls_after_error)
            return

        self.log(self.get_translation('found_videos_msg', count=len(video_files)))
        file_index = 0
        base_rtmp_url = self.rtmp_url.get().strip().rstrip('/')
        stream_key = self.stream_key.get().strip()
        full_rtmp_url = f"{base_rtmp_url}/{stream_key}"

        # Main loop: continues as long as streaming is active and not explicitly stopped
        while self.streaming_active and not self.stop_requested:
            # --- Loop/Index Management ---
            if file_index >= len(video_files):
                file_index = 0 # Wrap around
                if not self.streaming_active or self.stop_requested: break # Check flags before logging loop completion
                self.log(self.get_translation('loop_complete_msg'))

            current_file = video_files[file_index]
            try:
                # Use safer basename handling
                base_name = os.path.basename(current_file)
            except Exception:
                 # Provide a more informative error message
                base_name = self.get_translation('filename_encoding_error', index=file_index+1)
            self.log(self.get_translation('starting_file_msg', filename=base_name))

            # --- Clear switch flag for the new video ---
            self.switch_video_event.clear()

            # --- Build FFmpeg Command ---
            # (Command building logic remains the same as v3.3)
            cmd = [self.ffmpeg_path.get(), "-re", "-i", current_file]
            filter_complex_parts = []
            if self.add_watermark.get() and self.watermark_path.get(): # Check if path is set
                cmd.extend(["-i", self.watermark_path.get()])
                filter_complex_parts.append("[0:v][1:v]overlay=main_w-overlay_w-10:10")
            if filter_complex_parts:
                cmd.extend(["-filter_complex", ";".join(filter_complex_parts)])

            v_enc_full = self.video_encoder.get()
            v_enc = v_enc_full.split(" ")[0]
            cmd.extend(["-c:v", v_enc])
            common_params = ["-g", "60", "-pix_fmt", "yuv420p", "-max_muxing_queue_size", "1024"]
            if v_enc == "libx264":
                cmd.extend(["-preset", "veryfast", "-crf", "23", "-maxrate", "3500k", "-bufsize", "7000k"] + common_params)
            elif v_enc == "h264_nvenc":
                self.log(self.get_translation('nvenc_driver_warning'))
                cmd.extend(["-preset", "p5", "-tune", "hq", "-rc", "cbr", "-b:v", "3500k", "-maxrate", "4000k", "-bufsize", "7000k"] + common_params)
            elif v_enc == "h264_amf":
                self.log(self.get_translation('amd_amf_warning'))
                cmd.extend(["-quality", "balanced", "-rc", "cbr", "-b:v", "3500k", "-maxrate", "4000k", "-bufsize", "7000k"] + common_params)
            elif v_enc == "h264_qsv":
                self.log(self.get_translation('intel_qsv_warning'))
                cmd.extend(["-preset", "medium", "-look_ahead", "1", "-rc_mode", "CBR", "-b:v", "3500k", "-max_bitrate", "4000k", "-bufsize", "7000k"] + common_params)
            else: # Fallback to libx264 if unknown
                cmd.extend(["-c:v", "libx264"])
                cmd.extend(["-preset", "veryfast", "-crf", "23", "-maxrate", "3500k", "-bufsize", "7000k"] + common_params)
            a_enc_full = self.audio_handling.get()
            a_enc = a_enc_full.split(" ")[0]
            cmd.extend(["-c:a", a_enc])
            if a_enc == "aac":
                cmd.extend(["-b:a", "128k", "-ar", "44100", "-strict", "-2"])
            elif a_enc == "copy":
                self.log(self.get_translation('copying_audio_info'))
            cmd.extend(["-f", "flv", full_rtmp_url])
            self.log(self.get_translation('executing_command_msg', command=' '.join(cmd)))

            # --- Execute FFmpeg and Handle Output/Signals ---
            process_finished_normally = False
            ffmpeg_process_started = False # Flag to track if Popen was successful
            stderr_lines = [] # Store recent stderr lines for error context
            try:
                creationflags = 0
                if os.name == 'nt':
                    creationflags = subprocess.CREATE_NO_WINDOW # Hide console window on Windows
                # *** Critical: Set self.current_ffmpeg_process *only* after Popen succeeds ***
                local_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                    encoding='utf-8', errors='replace', creationflags=creationflags
                )
                self.current_ffmpeg_process = local_process # Assign to instance variable
                ffmpeg_process_started = True

                # Read stderr line by line without blocking indefinitely
                while self.streaming_active: # Check streaming_active frequently

                    # *** Check for signals FIRST before accessing the process object ***
                    if self.stop_requested:
                        self.log(self.get_translation('stop_detected_ffmpeg_output_msg'))
                        # Request termination if process is still running
                        if self.current_ffmpeg_process and self.current_ffmpeg_process.poll() is None:
                           self._request_ffmpeg_termination("stop")
                        break # Exit inner stderr reading loop

                    if self.switch_video_event.is_set():
                        self.log(self.get_translation('switch_detected_ffmpeg_output_msg'))
                         # Request termination if process is still running
                        if self.current_ffmpeg_process and self.current_ffmpeg_process.poll() is None:
                            self._request_ffmpeg_termination("switch")
                        break # Exit inner stderr reading loop

                    # *** Check if process ended on its own *before* reading ***
                    # Ensure process object exists before polling
                    if self.current_ffmpeg_process and self.current_ffmpeg_process.poll() is not None:
                         break # Process finished

                    # *** Read stderr only if process exists and hasn't finished ***
                    if self.current_ffmpeg_process:
                         try:
                             line = self.current_ffmpeg_process.stderr.readline()
                             if not line: # End of stream
                                 break
                             line = line.strip()
                             if line:
                                 self.log(self.get_translation('ffmpeg_output_log', line=line))
                                 stderr_lines.append(line)
                                 if len(stderr_lines) > 20: # Keep only last 20 lines
                                     stderr_lines.pop(0)
                         except Exception as read_err:
                             # Check if the error is due to the process being terminated AFTER the poll check above
                             if not self.current_ffmpeg_process or self.current_ffmpeg_process.poll() is not None:
                                 self.log(f"INFO: FFmpeg stderr read ended as process terminated.")
                             else:
                                 self.log(f"WARN: Error reading FFmpeg stderr: {read_err}")
                             break # Exit read loop on error or termination
                    else:
                         # Process became None unexpectedly or due to signal handling race condition (should be rare now)
                         self.log("INFO: FFmpeg process became None during stderr read, exiting loop.")
                         break

                # --- Post-Process Handling (after stderr loop) ---
                # Ensure cleanup happens even if stderr loop breaks early
                return_code = None
                if self.current_ffmpeg_process:
                    # Wait for the process to finish if it hasn't already (e.g., due to signal break)
                    try:
                         # Use a timeout to avoid blocking indefinitely if termination fails unexpectedly
                        self.current_ffmpeg_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                         self.log(f"WARN: Timeout waiting for FFmpeg process (PID: {self.current_ffmpeg_process.pid}) to exit after loop.")
                    except Exception as wait_err:
                         self.log(f"WARN: Error during final FFmpeg process wait: {wait_err}")
                    # Get final return code
                    return_code = self.current_ffmpeg_process.poll()


                # Check signals *again* after process finished/was terminated/waited upon
                if self.stop_requested:
                    self.log(self.get_translation('stop_detected_after_file_msg', filename=base_name))
                    break # Exit the main 'while self.streaming_active' loop

                if self.switch_video_event.is_set():
                    self.log(self.get_translation('switch_detected_after_file_msg', filename=base_name))
                    # Don't break the main loop, just continue to the next video
                    file_index += 1
                    self.log(self.get_translation('switching_to_next_video_msg'))
                    continue # Go to the next iteration of the main while loop

                # --- Handle Normal Exit / Errors ---
                if return_code == 0:
                    self.log(self.get_translation('stream_finished_success_msg', filename=base_name))
                    process_finished_normally = True
                # Check if process actually started before logging errors
                elif ffmpeg_process_started:
                     # Handle potential negative exit codes on Windows more gracefully
                    effective_code = return_code if return_code is not None else "N/A"
                    if os.name == 'nt' and return_code is not None and return_code < 0:
                         effective_code = return_code & 0xFFFFFFFF # Treat as unsigned 32-bit
                         self.log(f"WARN: FFmpeg exited with negative code {return_code}, interpreted as {effective_code}")

                    # Log error only if it wasn't due to a user stop/switch signal detected *before* the error
                    # (return_code might be non-zero due to termination signal)
                    if not self.stop_requested and not self.switch_video_event.is_set():
                         self.log(self.get_translation('ffmpeg_error_exit_msg', code=f"{return_code} ({effective_code})", filename=base_name))
                         error_context = "\n".join(stderr_lines) # Use captured stderr
                         self.log(self.get_translation('ffmpeg_error_context_msg', context=error_context))
                         self.log(self.get_translation('continuing_after_error_warn'))
                         time.sleep(3) # Pause briefly after an error before next file
                    else:
                         # Logged as stopped/switched, non-zero exit code is expected/acceptable
                         self.log(f"INFO: FFmpeg exited with code {return_code} after stop/switch request for {base_name}.")


            except FileNotFoundError:
                self.log(self.get_translation('ffmpeg_command_not_found_fatal', path=self.ffmpeg_path.get()))
                self.streaming_active = False # Stop loop on fatal error
                self.stop_requested = True    # Ensure loop exit condition met
            except Exception as e:
                self.log(self.get_translation('ffmpeg_unexpected_error_fatal', error=e))
                import traceback
                self.log(traceback.format_exc())
                self.streaming_active = False # Stop loop on fatal error
                self.stop_requested = True    # Ensure loop exit condition met
            finally:
                 # *** This is the primary place to set process handle to None ***
                 # Ensure it's cleared after wait()/poll() and error handling
                 self.current_ffmpeg_process = None
                 # Clear the switch flag here too, ready for the next potential video
                 # Although cleared at the start of the loop, clearing here adds safety
                 # self.switch_video_event.clear() # Decided against clearing here, start of loop is better

            # --- Loop Increment / Exit Check ---
            if not self.streaming_active or self.stop_requested:
                 # Check again in case flags changed during error handling/sleep
                 break
            elif process_finished_normally:
                 # Increment index only if the process finished without stop/switch/error request interrupting it mid-stream
                 file_index += 1
            # else: If process failed or was switched, loop continues without incrementing index (unless switched, then 'continue' was used)


        # --- Loop Exit Logging ---
        if self.stop_requested:
            self.log(self.get_translation('exiting_loop_after_file_msg'))
        elif self.streaming_active:
            # If loop exits while streaming_active is true and stop wasn't requested, it was unexpected
            self.log(self.get_translation('loop_terminated_unexpectedly_warn'))
            if self.root and self.root.winfo_exists(): # Schedule UI reset
                 self.root.after(100, self.reset_controls_after_error)

        self.log(self.get_translation('stream_thread_finished_msg'))
        # Final check to reset controls if the thread ends but stop wasn't explicitly called (e.g., error)
        if not self.stop_requested and self.root and self.root.winfo_exists():
             # Use after_idle to ensure this runs after any pending events
             self.root.after_idle(self.reset_controls_if_needed)


    def reset_controls_after_error(self):
        """Resets controls specifically after an error terminates the loop."""
        if self.root and self.root.winfo_exists(): # Check root
            # Only reset if streaming is not supposed to be active anymore
            # Check both flags for robustness
            if self.streaming_active or self.stop_requested:
                self.streaming_active = False
                self.stop_requested = False # Reset stop flag
            self.switch_video_event.clear() # Reset switch flag
            self.update_control_states()
            self.log(self.get_translation('buttons_reset_after_error_warn'))

    def reset_controls_if_needed(self):
        """Called after stream thread ends to reset UI if stop wasn't requested."""
        if self.root and self.root.winfo_exists():
             # If streaming_active is still True here, it means the loop ended without stop_requested
             # This usually indicates an error condition that wasn't caught properly or list exhaustion
             if self.streaming_active and not self.stop_requested:
                  self.log("WARN: reset_controls_if_needed called while streaming_active=True and stop_requested=False. Resetting UI.")
                  self.reset_controls_after_error() # Treat as error state
             elif not self.streaming_active and not self.stop_requested:
                 # If streaming stopped naturally (e.g. loop ended without error but wasn't explicitly stopped by user)
                 # Ensure the UI reflects the non-streaming state.
                 self.update_control_states()


    def on_closing(self):
        if self.streaming_active:
            if messagebox.askyesno(self.get_translation('confirm_exit_title'), self.get_translation('confirm_exit_msg')):
                self.stop_streaming()
                # Give stop_streaming a moment to act before destroying root
                self.root.after(500, self.root.destroy)
            # else: Do nothing if user selects 'No'
        else:
            # Ensure thread cleanup even if not streaming but thread somehow exists
            if self.stream_thread and self.stream_thread.is_alive():
                self.log("WARN: Closing window with inactive stream thread.")
                # Give it a very short time to exit if it's stuck somehow
                self.stream_thread.join(timeout=0.2)
            self.root.destroy()

# --- Run the application ---
if __name__ == "__main__":
    main_root = tk.Tk()
    app = StreamerApp(main_root)
    main_root.protocol("WM_DELETE_WINDOW", app.on_closing)
    try:
        main_root.mainloop()
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Closing application.")
        # Attempt graceful shutdown if app object exists
        if app and hasattr(app, 'on_closing'):
             app.on_closing()
        elif main_root and main_root.winfo_exists():
             main_root.destroy()
