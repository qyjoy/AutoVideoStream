import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, Menu
import subprocess
import threading
import os
import glob
import time
import sys
import json # Used for potentially saving/loading config later, not strictly needed now
import webbrowser
# --- Constants ---
VIDEO_EXTENSIONS = ["*.mp4", "*.mkv", "*.mov", "*.avi", "*.flv"]
FFMPEG_DEFAULT_PATH = "ffmpeg" # Assume ffmpeg is in PATH
DEFAULT_LANG = "zh_CN"
VERSION = '3.1 By QyJoy'
# --- Main Application Class ---
class StreamerApp:
    def __init__(self, root):
        self.root = root
        self.setup_language() # MUST be first
        self.root.title(self.get_translation('app_title'))
        self.root.geometry("420x500")
        self.themes = {
            "默认 (Default)": {"bg": "#F0F0F0", "fg": "black", "widget_bg": "#FFFFFF", "widget_fg": "black", "button_bg": "#E0E0E0", "button_fg": "black", "disabled_fg": "#A0A0A0", "log_bg": "#FFFFFF", "log_fg": "black", "select_bg": "#0078D7", "select_fg": "white"},
            "夜间 (Night)": {"bg": "#2E2E2E", "fg": "white", "widget_bg": "#3C3C3C", "widget_fg": "white", "button_bg": "#505050", "button_fg": "white", "disabled_fg": "#808080", "log_bg": "#1E1E1E", "log_fg": "white", "select_bg": "#5A5A5A", "select_fg": "white"},
            "蓝调 (Blue)": {"bg": "#E3F2FD", "fg": "#0D47A1", "widget_bg": "#BBDEFB", "widget_fg": "#0D47A1", "button_bg": "#90CAF9", "button_fg": "#0D47A1", "disabled_fg": "#64B5F6", "log_bg": "#FFFFFF", "log_fg": "#1976D2", "select_bg": "#64B5F6", "select_fg": "white"},
            "炫彩 (Vibrant)": {"bg": "#FFF8E1", "fg": "#E65100", "widget_bg": "#FFECB3", "widget_fg": "#E65100", "button_bg": "#FFB74D", "button_fg": "#BF360C", "disabled_fg": "#FFCC80", "log_bg": "#FFFDE7", "log_fg": "#F57C00", "select_bg": "#FFA726", "select_fg": "black"},
            "绿色 (Green)": {"bg": "#E8F5E9", "fg": "#1B5E20", "widget_bg": "#C8E6C9", "widget_fg": "#1B5E20", "button_bg": "#A5D6A7", "button_fg": "#1B5E20", "disabled_fg": "#81C784", "log_bg": "#F1F8E9", "log_fg": "#388E3C", "select_bg": "#66BB6A", "select_fg": "white"},
            "粉色 (Pink)": {"bg": "#FCE4EC", "fg": "#880E4F", "widget_bg": "#F8BBD0", "widget_fg": "#880E4F", "button_bg": "#F48FB1", "button_fg": "#880E4F", "disabled_fg": "#F06292", "log_bg": "#FBE9E7", "log_fg": "#AD1457", "select_bg": "#EC407A", "select_fg": "white"}        
        }
        self.selected_theme = tk.StringVar(value="默认 (Default)")

        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        if 'clam' in available_themes: self.style.theme_use('clam')
        elif 'alt' in available_themes: self.style.theme_use('alt')

        self.rtmp_url = tk.StringVar()
        self.stream_key = tk.StringVar()
        self.video_folder = tk.StringVar()
        self.watermark_path = tk.StringVar()
        self.ffmpeg_path = tk.StringVar(value=FFMPEG_DEFAULT_PATH)
        self.add_watermark = tk.BooleanVar()
        self.video_encoder = tk.StringVar(value="libx264 (CPU)")
        self.audio_handling = tk.StringVar(value="aac (Re-encode)")
        self.streaming_active = False
        self.stream_thread = None
        self.current_ffmpeg_process = None

        # --- GUI Setup ---
        self.create_menu() # Creates menu structure
        self.create_widgets() # Creates widgets, references are stored
        self.apply_theme() # Apply default theme
        # self.store_translatable_widgets() # No longer needed if refs stored in create_widgets

    def setup_language(self):
        self.current_lang = tk.StringVar(value=DEFAULT_LANG)
        # --- Translations Dictionary (ensure all keys exist for both languages) ---
        self.translations = {
            "zh_CN": {
                "app_title": "AutoVideoStreamerGUI(自动循环推流)"+VERSION, "menu_theme": "主题 (Theme)",
                "lang_chinese": "简体中文", "lang_english": "English", "ffmpeg_path_label": "FFmpeg路径:", "browse_button": "浏览",
                "rtmp_url_label": "RTMP 推流地址:", "stream_key_label": "推流码 (Stream Key):", "video_folder_label": "视频文件夹:",
                "add_watermark_check": "添加水印", "video_encoder_label": "视频编码器:", "audio_handling_label": "音频处理:",
                "start_button": "开始推流", "stop_button": "停止推流", "log_output_label": "日志输出","github_button": "Github发布页",#3.1 added
                "error_title": "错误", "info_title": "信息", "warn_title": "警告", "confirm_exit_title": "退出确认",
                "ffmpeg_not_found_msg": "未在路径 '{path}' 找到 ffmpeg.exe。请指定正确路径或确保其在系统 PATH 中。",
                "ffmpeg_execution_error_msg": "无法执行 FFmpeg ('{path}'). 请确保已安装并在 PATH 中，或指定正确的 .exe 文件路径。\n错误详情: {error}",
                "rtmp_url_invalid_msg": "RTMP 推流地址必须以 rtmp:// 开头且不能为空。", "stream_key_empty_msg": "推流码 (Stream Key) 不能为空。",
                "video_folder_invalid_msg": "请选择一个有效的视频文件夹。", "watermark_invalid_msg": "请选择一个有效的水印图片文件。",
                "stream_already_running_msg": "推流已经在运行中。", "stream_not_running_msg": "推流尚未开始。",
                "starting_stream_msg": "开始启动推流循环...", "stopping_stream_msg": "正在尝试停止推流...",
                "terminating_ffmpeg_msg": "正在终止当前的 FFmpeg 进程 (PID: {pid})...", "ffmpeg_terminated_msg": "FFmpeg 进程已正常终止。",
                "ffmpeg_terminate_failed_msg": "FFmpeg 进程未能正常终止，强制结束...", "ffmpeg_killed_msg": "FFmpeg 进程已被强制结束。",
                "ffmpeg_terminate_exception_msg": "无法终止 FFmpeg 进程: {error}", "stream_thread_still_active_warn": "推流线程在停止请求后仍然活跃。",
                "user_stop_completed_msg": "用户请求停止推流完成。", "no_videos_found_error": "在指定文件夹 '{folder}' 未找到视频文件 ({exts})。",
                "found_videos_msg": "找到 {count} 个视频文件。开始循环播放。", "loop_complete_msg": "完成一轮播放，从头开始下一轮。",
                "starting_file_msg": "--- 开始推流: {filename} ---", "copying_audio_info": "尝试直接复制音频流。如果源音频与目标不兼容可能会失败。",
                "executing_command_msg": "执行命令: {command}", "ffmpeg_output_log": "FFMPEG: {line}",
                "stop_detected_ffmpeg_output_msg": "在 FFmpeg 输出期间检测到停止请求。", "stop_detected_after_file_msg": "推流 {filename} 在结束后检测到停止信号。",
                "stream_finished_success_msg": "--- 完成推流: {filename} (成功) ---", "ffmpeg_error_exit_msg": "--- FFmpeg 错误退出 (代码 {code}) 对于: {filename} ---",
                "ffmpeg_error_context_msg": "FFmpeg 可能的错误信息:\n{context}", "continuing_after_error_warn": "检测到错误，将尝试播放列表中的下一个文件。",
                "ffmpeg_command_not_found_fatal": "FATAL ERROR: '{path}' 命令未找到。请检查 FFmpeg 路径设置。",
                "ffmpeg_unexpected_error_fatal": "FATAL ERROR: 运行 FFmpeg 时发生意外错误: {error}", "exiting_loop_after_file_msg": "在文件处理完成后退出推流循环。",
                "loop_terminated_unexpectedly_warn": "WARN: 推流循环意外终止。", "buttons_reset_after_error_warn": "WARN: 推流循环已终止 (可能由于错误)。按钮已重置。",
                "stream_thread_finished_msg": "INFO: 推流线程结束。", "confirm_exit_msg": "推流正在进行中。\n您确定要停止推流并退出吗？",
                "nvenc_driver_warning": "WARN: 检测到 NVENC 编码器。请确保您的 NVIDIA 驱动版本 >= 570.0 以获得最佳兼容性，否则可能出错。",
                "amd_amf_warning": "WARN: 使用 h264_amf, 请确保驱动和 FFmpeg 支持良好。参数可能需调整。",
                "intel_qsv_warning": "WARN: 使用 h264_qsv, 请确保驱动和 FFmpeg 支持良好。参数可能需调整。",
                "ffmpeg_verified_msg": "INFO: 成功找到并验证 FFmpeg。", "search_video_error_msg": "ERROR: 搜索视频文件时出错: {error} (路径: {folder})",
                "filename_encoding_error": "[文件名编码错误 {index}]",
            },
            "en_US": {
                "app_title": "AutoVideoStreamerGUI"+VERSION, "menu_theme": "Theme",
                "lang_chinese": "简体中文", "lang_english": "English", "ffmpeg_path_label": "FFmpeg Path:", "browse_button": "Browse",
                "rtmp_url_label": "RTMP URL:", "stream_key_label": "Stream Key:", "video_folder_label": "Video Folder:",
                "add_watermark_check": "Add Watermark", "video_encoder_label": "Video Encoder:", "audio_handling_label": "Audio Handling:",
                "start_button": "Start Streaming", "stop_button": "Stop Streaming", "log_output_label": "Log Output", "github_button": "Github",
                "error_title": "Error", "info_title": "Info", "warn_title": "Warning", "confirm_exit_title": "Confirm Exit",
                "ffmpeg_not_found_msg": "ffmpeg.exe not found at '{path}'. Please specify the correct path or ensure it's in the system PATH.",
                "ffmpeg_execution_error_msg": "Failed to execute FFmpeg ('{path}'). Ensure it's installed and in PATH, or specify the correct .exe path.\nError details: {error}",
                "rtmp_url_invalid_msg": "RTMP URL must start with rtmp:// and cannot be empty.", "stream_key_empty_msg": "Stream Key cannot be empty.",
                "video_folder_invalid_msg": "Please select a valid video folder.", "watermark_invalid_msg": "Please select a valid watermark image file.",
                "stream_already_running_msg": "Streaming is already in progress.", "stream_not_running_msg": "Streaming has not started yet.",
                "starting_stream_msg": "Starting stream loop...", "stopping_stream_msg": "Attempting to stop streaming...",
                "terminating_ffmpeg_msg": "Terminating current FFmpeg process (PID: {pid})...", "ffmpeg_terminated_msg": "FFmpeg process terminated gracefully.",
                "ffmpeg_terminate_failed_msg": "FFmpeg process did not terminate gracefully, killing...", "ffmpeg_killed_msg": "FFmpeg process killed.",
                "ffmpeg_terminate_exception_msg": "Could not terminate FFmpeg process: {error}", "stream_thread_still_active_warn": "Stream thread still active after stop request.",
                "user_stop_completed_msg": "Streaming stop requested by user completed.", "no_videos_found_error": "ERROR: No video files found in the specified folder '{folder}' ({exts}).",
                "found_videos_msg": "INFO: Found {count} video files. Starting loop.", "loop_complete_msg": "INFO: Completed one cycle, starting next loop.",
                "starting_file_msg": "--- Starting stream for: {filename} ---", "copying_audio_info": "INFO: Attempting to copy audio stream. May fail if incompatible.",
                "executing_command_msg": "Executing: {command}", "ffmpeg_output_log": "FFMPEG: {line}",
                "stop_detected_ffmpeg_output_msg": "INFO: Stop requested detected during FFmpeg output.", "stop_detected_after_file_msg": "INFO: Stop signal detected after processing {filename}.",
                "stream_finished_success_msg": "--- Finished streaming: {filename} (Success) ---", "ffmpeg_error_exit_msg": "--- FFmpeg exited with error (code {code}) for: {filename} ---",
                "ffmpeg_error_context_msg": "FFmpeg potential error context:\n{context}", "continuing_after_error_warn": "WARN: Error detected, attempting next file in playlist.",
                "ffmpeg_command_not_found_fatal": "FATAL ERROR: '{path}' command not found. Check FFmpeg path setting.",
                "ffmpeg_unexpected_error_fatal": "FATAL ERROR: An unexpected error occurred running FFmpeg: {error}", "exiting_loop_after_file_msg": "INFO: Exiting stream loop after file completion.",
                "loop_terminated_unexpectedly_warn": "WARN: Stream loop terminated unexpectedly.", "buttons_reset_after_error_warn": "WARN: Stream loop terminated (possibly due to error). Buttons reset.",
                "stream_thread_finished_msg": "INFO: Stream thread finished.", "confirm_exit_msg": "Streaming is in progress.\nAre you sure you want to stop streaming and exit?",
                "nvenc_driver_warning": "WARN: NVENC encoder selected. Ensure your NVIDIA driver version is >= 570.0 for best compatibility, otherwise errors may occur.",
                "amd_amf_warning": "WARN: Using h264_amf, ensure drivers and FFmpeg support are correct. Parameters might need tuning.",
                "intel_qsv_warning": "WARN: Using h264_qsv, ensure drivers and FFmpeg support are correct. Parameters might need tuning.",
                "ffmpeg_verified_msg": "INFO: Found and verified FFmpeg successfully.", "search_video_error_msg": "ERROR: Error searching for video files: {error} (Path: {folder})",
                "filename_encoding_error": "[Filename Encoding Error {index}]",
            }
        }
    def get_translation(self, key, **kwargs):
        lang = self.current_lang.get()
        try:
            # Fallback to default language if key is missing in current language
            base_string = self.translations.get(lang, {}).get(key)
            if base_string is None:
                 base_string = self.translations.get(DEFAULT_LANG, {}).get(key, f"<{key}>")

            return base_string.format(**kwargs)
        except KeyError:
            print(f"Warning: Translation key '{key}' not found for language '{lang}' or default.")
            return f"<{key}>"
        except Exception as e:
             print(f"Warning: Error formatting translation key '{key}': {e}")
             return f"<{key}> (Format Error)"

    def create_menu(self):
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)

        # ============== 语言菜单固定标题 ============== #
        self.lang_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="语言(Language)", menu=self.lang_menu)  # 固定标题

        # ============== 主题菜单固定标题 ============== #
        self.theme_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="主题(Theme)", menu=self.theme_menu)    # 固定标题

        # 添加语言选项
        self.lang_menu.add_radiobutton(
            label=self.get_translation('lang_chinese'),
            variable=self.current_lang,
            value='zh_CN',
            command=self.switch_language
        )
        self.lang_menu.add_radiobutton(
            label=self.get_translation('lang_english'),
            variable=self.current_lang,
            value='en_US',
            command=self.switch_language
        )

        # 添加主题选项
        for theme_name in self.themes:
            self.theme_menu.add_radiobutton(
                label=theme_name,  # 主题名称保持原有双语格式
                variable=self.selected_theme,
                command=self.apply_theme
            )

    #                         switch_language
    # ========================================================================
    def switch_language(self):
            # 1. 更新窗口标题
        self.root.title(self.get_translation('app_title'))

        # 2. 更新语言菜单项标签（不再更新菜单标题）
        try:
            self.lang_menu.entryconfig(0, label=self.get_translation('lang_chinese'))
            self.lang_menu.entryconfig(1, label=self.get_translation('lang_english'))
        except Exception as e:
            print(f"语言菜单更新错误: {e}")


        #更换语言重载组件 3. Update Widget Texts using stored references (assuming they exist)
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
            self.github_button.config(text=self.get_translation('github_button'))#3.1added
            self.log_frame.config(text=self.get_translation('log_output_label'))
            # Add any other widgets that need text updates here
        except AttributeError as e:
            print(f"ERROR: Widget reference missing during language switch: {e}")

        # 4. Re-apply theme (optional but can help ensure consistency)
        self.apply_theme()
    # ========================================================================

    def apply_theme(self):
        # --- (Theme application logic - unchanged) ---
        theme_name = self.selected_theme.get()
        theme = self.themes.get(theme_name, self.themes["默认 (Default)"])
        bg=theme["bg"]; fg=theme["fg"]; widget_bg=theme["widget_bg"]; widget_fg=theme["widget_fg"]
        button_bg=theme["button_bg"]; button_fg=theme["button_fg"]; log_bg=theme["log_bg"]; log_fg=theme["log_fg"]
        select_bg=theme["select_bg"]; select_fg=theme["select_fg"]; disabled_fg=theme["disabled_fg"]
        self.root.config(bg=bg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background=button_bg, foreground=button_fg, padding=5)
        self.style.map("TButton", background=[('active', select_bg), ('disabled', button_bg)], foreground=[('active', select_fg), ('disabled', disabled_fg)])
        self.style.configure("TEntry", fieldbackground=widget_bg, foreground=widget_fg, insertcolor=widget_fg)
        self.style.map("TEntry", fieldbackground=[('disabled', bg)], foreground=[('disabled', disabled_fg)])
        self.style.configure("TCombobox", fieldbackground=widget_bg, foreground=widget_fg, background=button_bg, arrowcolor=fg)
        self.style.map("TCombobox", fieldbackground=[('readonly', widget_bg), ('disabled', bg)], foreground=[('readonly', widget_fg), ('disabled', disabled_fg)], selectbackground=[('readonly', select_bg)], selectforeground=[('readonly', select_fg)])
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.map("TCheckbutton", background=[('active', bg)], foreground=[('active', fg), ('disabled', disabled_fg)])
        self.style.configure("TLabelFrame", background=bg, foreground=fg, bordercolor=fg)
        self.style.configure("TLabelFrame.Label", background=bg, foreground=fg)
        if hasattr(self, 'log_area'):
            original_state = self.log_area['state']
            try: # Adding try block for safety during theme change
                self.log_area.config(state=tk.NORMAL)
                self.log_area.config(bg=log_bg, fg=log_fg, selectbackground=select_bg, selectforeground=select_fg, insertbackground=fg)
            finally:
                self.log_area.config(state=original_state) # Ensure state is reset
        if hasattr(self, 'input_frame'): # Check if widgets exist before configuring
            for widget in self.input_frame.winfo_children(): widget.configure(style=widget.winfo_class())
            for widget in self.control_frame.winfo_children(): widget.configure(style=widget.winfo_class())
            for widget in self.log_frame.winfo_children():
                 if isinstance(widget, (ttk.Frame, ttk.Label)) : widget.configure(style=widget.winfo_class())
            self.toggle_watermark_entry()
            self.update_control_states()


    def create_widgets(self):
        # --- Frame for Inputs ---
        self.input_frame = ttk.Frame(self.root, padding="10")
        self.input_frame.pack(pady=0, padx=1, fill=tk.X)

        # Store references to widgets needing translation when creating them
        self.ffmpeg_label = ttk.Label(self.input_frame, text=self.get_translation('ffmpeg_path_label'))
        self.ffmpeg_label.grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.ffmpeg_entry = ttk.Entry(self.input_frame, textvariable=self.ffmpeg_path, width=50)
        self.ffmpeg_entry.grid(row=0, column=1, padx=5, pady=3, sticky=tk.EW)
        self.ffmpeg_browse_btn = ttk.Button(self.input_frame, text=self.get_translation('browse_button'), command=self.browse_ffmpeg)
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
        self.folder_browse_btn = ttk.Button(self.input_frame, text=self.get_translation('browse_button'), command=self.browse_folder)
        self.folder_browse_btn.grid(row=3, column=2, padx=5, pady=3)

        self.watermark_check = ttk.Checkbutton(self.input_frame, text=self.get_translation('add_watermark_check'), variable=self.add_watermark, command=self.toggle_watermark_entry)
        self.watermark_check.grid(row=4, column=0, padx=5, pady=3, sticky=tk.W)
        self.watermark_entry = ttk.Entry(self.input_frame, textvariable=self.watermark_path, width=50, state=tk.DISABLED)
        self.watermark_entry.grid(row=4, column=1, padx=5, pady=3, sticky=tk.EW)
        self.watermark_browse_btn = ttk.Button(self.input_frame, text=self.get_translation('browse_button'), command=self.browse_watermark, state=tk.DISABLED)
        self.watermark_browse_btn.grid(row=4, column=2, padx=5, pady=3)

        self.video_encoder_label = ttk.Label(self.input_frame, text=self.get_translation('video_encoder_label'))
        self.video_encoder_label.grid(row=5, column=0, padx=5, pady=3, sticky=tk.W)
        self.video_encoder_combo = ttk.Combobox(self.input_frame, textvariable=self.video_encoder,
                                          values=["libx264 (CPU)", "h264_nvenc (Nvidia)", "h264_amf (AMD)", "h264_qsv (Intel)"],
                                          state="readonly")
        self.video_encoder_combo.grid(row=5, column=1, columnspan=2, padx=5, pady=1, sticky=tk.EW)

        self.audio_handling_label = ttk.Label(self.input_frame, text=self.get_translation('audio_handling_label'))
        self.audio_handling_label.grid(row=6, column=0, padx=5, pady=1, sticky=tk.W)
        self.audio_handling_combo = ttk.Combobox(self.input_frame, textvariable=self.audio_handling,
                                            values=["aac (Re-encode)", "copy (Try Direct Copy)"],
                                            state="readonly")
        self.audio_handling_combo.grid(row=6, column=1, columnspan=2, padx=5, pady=1, sticky=tk.EW)

        self.input_frame.columnconfigure(1, weight=1)

        # --- Frame for Controls ---
        self.control_frame = ttk.Frame(self.root, padding="10")
        self.control_frame.pack(pady=1, padx=1, fill=tk.X)

        self.start_button = ttk.Button(self.control_frame, text=self.get_translation('start_button'), command=self.start_streaming)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=1)
        self.stop_button = ttk.Button(self.control_frame, text=self.get_translation('stop_button'), command=self.stop_streaming, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=1)
        #3.1Added
        self.github_button = ttk.Button(self.control_frame, text=self.get_translation('github_button'), command=lambda: webbrowser.open("https://github.com/qyjoy/AutoVideoStream"))
        self.github_button.pack(side=tk.LEFT, padx=5, pady=1)

        # --- Frame for Log Output ---
        self.log_frame = ttk.LabelFrame(self.root, text=self.get_translation('log_output_label'), padding="10")
        self.log_frame.pack(pady=3, padx=5, fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(
            self.log_frame, 
            wrap=tk.WORD, 
            height=10, 
            state=tk.DISABLED,
            # ============== 新增性能优化参数 ============== #
            maxundo=100,  # 限制撤销记录
            undo=True,     # 启用撤销功能用于高效删除
            autoseparators=True,  # 自动插入分隔符
            blockcursor=False     # 禁用块状光标
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        # Apply initial theme colors to log area right after creation - Moved to end of apply_theme
    def log(self, message):
        def _log_on_main_thread():
            current_state = self.log_area['state']
            try:
                self.log_area.config(state=tk.NORMAL)
                                # ============== 新增日志截断逻辑 ============== #
                # 先插入新日志
                self.log_area.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
                
                # 获取当前总行数
                line_count = int(self.log_area.index('end-1c').split('.')[0])
                
                # 维护最大1000行日志
                if line_count > 1000:
                    # 计算需要删除的超额行数
                    excess = line_count - 1000
                    
                    # 使用高效方式删除最老日志（直接操作文本块）
                    self.log_area.delete(1.0, f"{excess + 1}.0 lineend")
                    
                    # 可选：定期整理内存（每20次截断执行一次）
                    if excess % 20 == 0:
                        self.log_area.edit_reset()  # 清除撤销历史释放内存
                # 保持滚动到底部
                self.log_area.see(tk.END)
                self.log_area.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
                self.log_area.see(tk.END)
            finally:
                self.log_area.config(state=current_state)
        self.root.after(0, _log_on_main_thread)
        print(message)

    def browse_ffmpeg(self):
        path = filedialog.askopenfilename(title="Select ffmpeg.exe", filetypes=[("Executable", "*.exe"), ("All Files", "*.*")])
        if path: self.ffmpeg_path.set(path)

    def browse_folder(self):
        path = filedialog.askdirectory(title=self.get_translation('video_folder_label'))
        if path: self.video_folder.set(path)

    def browse_watermark(self):
        path = filedialog.askopenfilename(title=self.get_translation('add_watermark_check'), filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")])
        if path: self.watermark_path.set(path)

    def toggle_watermark_entry(self):
        # Check if style object exists before using it
        if not hasattr(self, 'style'): return

        theme = self.themes.get(self.selected_theme.get(), self.themes["默认 (Default)"])
        disabled_bg = theme["bg"]
        disabled_fg = theme["disabled_fg"]

        # Check if widgets exist before configuring them
        if hasattr(self, 'watermark_entry') and hasattr(self, 'watermark_browse_btn'):
            if self.add_watermark.get():
                self.watermark_entry.config(state=tk.NORMAL)
                self.watermark_browse_btn.config(state=tk.NORMAL)
                self.style.map("TEntry", fieldbackground=[('disabled', disabled_bg)], foreground=[('disabled', disabled_fg)])
                self.watermark_entry.config(style="TEntry")
            else:
                self.watermark_entry.config(state=tk.DISABLED)
                self.watermark_browse_btn.config(state=tk.DISABLED)
                self.watermark_path.set("")
                self.style.map("TEntry", fieldbackground=[('disabled', disabled_bg)], foreground=[('disabled', disabled_fg)])
                self.watermark_entry.config(style="TEntry")

            self.style.map("TButton", background=[('active', theme["select_bg"]), ('disabled', theme["button_bg"])], foreground=[('active', theme["select_fg"]), ('disabled', disabled_fg)])
            self.watermark_browse_btn.config(style="TButton")


    def update_control_states(self):
        # Check if widgets exist before configuring
        if not all(hasattr(self, w) for w in [
            'start_button', 'stop_button', 'video_encoder_combo', 'audio_handling_combo',
            'ffmpeg_entry', 'ffmpeg_browse_btn', 'rtmp_entry', 'key_entry',
            'folder_entry', 'folder_browse_btn', 'watermark_check',
            'watermark_entry', 'watermark_browse_btn'
        ]):
            return # Don't try to configure if widgets aren't created yet

        if self.streaming_active:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.video_encoder_combo.config(state=tk.DISABLED)
            self.audio_handling_combo.config(state=tk.DISABLED)
            self.ffmpeg_entry.config(state=tk.DISABLED)
            self.ffmpeg_browse_btn.config(state=tk.DISABLED)
            self.rtmp_entry.config(state=tk.DISABLED)
            self.key_entry.config(state=tk.DISABLED)
            self.folder_entry.config(state=tk.DISABLED)
            self.folder_browse_btn.config(state=tk.DISABLED)
            self.watermark_check.config(state=tk.DISABLED)
            # Watermark entry/button state depends on checkbutton, but disable anyway
            self.watermark_entry.config(state=tk.DISABLED)
            self.watermark_browse_btn.config(state=tk.DISABLED)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.video_encoder_combo.config(state="readonly")
            self.audio_handling_combo.config(state="readonly")
            self.ffmpeg_entry.config(state=tk.NORMAL)
            self.ffmpeg_browse_btn.config(state=tk.NORMAL)
            self.rtmp_entry.config(state=tk.NORMAL)
            self.key_entry.config(state=tk.NORMAL)
            self.folder_entry.config(state=tk.NORMAL)
            self.folder_browse_btn.config(state=tk.NORMAL)
            self.watermark_check.config(state=tk.NORMAL)
            self.toggle_watermark_entry() # Set watermark state based on checkbutton


    # --- Streaming Logic (validate_inputs, start_streaming, stop_streaming, stream_loop - mostly unchanged logic, ensure translations used) ---
    def validate_inputs(self):
        # (Using get_translation - unchanged from previous)
        ffmpeg_path_val = self.ffmpeg_path.get()
        if not os.path.exists(ffmpeg_path_val) and ffmpeg_path_val != FFMPEG_DEFAULT_PATH:
             messagebox.showerror(self.get_translation('error_title'), self.get_translation('ffmpeg_not_found_msg', path=ffmpeg_path_val)); return False
        if ffmpeg_path_val == FFMPEG_DEFAULT_PATH or not os.path.exists(ffmpeg_path_val):
             try:
                 startupinfo = None
                 if os.name == 'nt': startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startupinfo.wShowWindow = subprocess.SW_HIDE
                 subprocess.run([ffmpeg_path_val, "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                 self.log(self.get_translation('ffmpeg_verified_msg'))
             except (FileNotFoundError, subprocess.CalledProcessError) as e:
                 messagebox.showerror(self.get_translation('error_title'), self.get_translation('ffmpeg_execution_error_msg', path=ffmpeg_path_val, error=e)); return False
        rtmp_url_val = self.rtmp_url.get().strip(); stream_key_val = self.stream_key.get().strip()
        if not rtmp_url_val or not rtmp_url_val.lower().startswith("rtmp://"): messagebox.showerror(self.get_translation('error_title'), self.get_translation('rtmp_url_invalid_msg')); return False
        if not stream_key_val: messagebox.showerror(self.get_translation('error_title'), self.get_translation('stream_key_empty_msg')); return False
        if not self.video_folder.get() or not os.path.isdir(self.video_folder.get()): messagebox.showerror(self.get_translation('error_title'), self.get_translation('video_folder_invalid_msg')); return False
        if self.add_watermark.get() and (not self.watermark_path.get() or not os.path.isfile(self.watermark_path.get())): messagebox.showerror(self.get_translation('error_title'), self.get_translation('watermark_invalid_msg')); return False
        return True

    def start_streaming(self):
        # (Unchanged logic, calls update_control_states)
        if not self.validate_inputs(): return
        if self.streaming_active: self.log(self.get_translation('stream_already_running_msg')); return
        self.streaming_active = True
        self.update_control_states()
        self.log(self.get_translation('starting_stream_msg'))
        self.stream_thread = threading.Thread(target=self.stream_loop, daemon=True); self.stream_thread.start()

    def stop_streaming(self):
        # (Unchanged logic, calls update_control_states via _finalize_stop)
        if not self.streaming_active: self.log(self.get_translation('stream_not_running_msg')); return
        self.log(self.get_translation('stopping_stream_msg')); self.streaming_active = False
        if self.current_ffmpeg_process and self.current_ffmpeg_process.poll() is None:
            try:
                self.log(self.get_translation('terminating_ffmpeg_msg', pid=self.current_ffmpeg_process.pid)); self.current_ffmpeg_process.terminate()
                try: self.current_ffmpeg_process.wait(timeout=3); self.log(self.get_translation('ffmpeg_terminated_msg'))
                except subprocess.TimeoutExpired:
                    self.log(self.get_translation('ffmpeg_terminate_failed_msg')); self.current_ffmpeg_process.kill()
                    try: self.current_ffmpeg_process.wait(timeout=1)
                    except Exception: pass
                    self.log(self.get_translation('ffmpeg_killed_msg'))
            except Exception as e: self.log(self.get_translation('ffmpeg_terminate_exception_msg', error=e))
        self.current_ffmpeg_process = None
        def _finalize_stop():
            if self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=0.5)
                if self.stream_thread.is_alive(): self.log(self.get_translation('stream_thread_still_active_warn'))
            self.update_control_states()
            self.log(self.get_translation('user_stop_completed_msg'))
        self.root.after(100, _finalize_stop)


    def stream_loop(self):
        # (FFmpeg command and loop logic - unchanged, uses translations for logging)
        video_files = []; folder = self.video_folder.get()
        try:
            safe_folder = folder
            if os.name == 'nt':
                try: safe_folder = safe_folder.encode(sys.getfilesystemencoding(), 'surrogateescape').decode('utf-8', 'replace')
                except Exception: self.log(f"WARN: Could not fully normalize folder path encoding: {folder}")
            for ext in VIDEO_EXTENSIONS: video_files.extend(glob.iglob(os.path.join(safe_folder, ext)))
        except Exception as e: self.log(self.get_translation('search_video_error_msg', error=e, folder=folder)); self.root.after(100, self.reset_controls_after_error); return
        video_files = list(video_files)
        if not video_files: self.log(self.get_translation('no_videos_found_error', folder=folder, exts=', '.join(VIDEO_EXTENSIONS))); self.root.after(100, self.reset_controls_after_error); return
        self.log(self.get_translation('found_videos_msg', count=len(video_files))); file_index = 0
        base_rtmp_url = self.rtmp_url.get().strip().rstrip('/'); stream_key = self.stream_key.get().strip(); full_rtmp_url = f"{base_rtmp_url}/{stream_key}"
        while self.streaming_active:
            if file_index >= len(video_files): file_index = 0; self.log(self.get_translation('loop_complete_msg')) # ; time.sleep(2)
            current_file = video_files[file_index]
            try: base_name = os.path.basename(current_file)
            except Exception: base_name = self.get_translation('filename_encoding_error', index=file_index+1)
            self.log(self.get_translation('starting_file_msg', filename=base_name))
            cmd = [self.ffmpeg_path.get(), "-re", "-i", current_file]; filter_complex_parts = []
            if self.add_watermark.get(): cmd.extend(["-i", self.watermark_path.get()]); filter_complex_parts.append("[0:v][1:v]overlay=W-w-10:10")
            if filter_complex_parts: cmd.extend(["-filter_complex", ";".join(filter_complex_parts)])
            v_enc_full = self.video_encoder.get(); v_enc = v_enc_full.split(" ")[0]; cmd.extend(["-c:v", v_enc])
            # --- Video Encoder Params ---
            common_params = ["-g", "60", "-pix_fmt", "yuv420p"] # Common params for compatibility
            if v_enc == "libx264": cmd.extend(["-preset", "veryfast", "-crf", "23", "-maxrate", "3500k", "-bufsize", "7000k"] + common_params)
            elif v_enc == "h264_nvenc":
                self.log(self.get_translation('nvenc_driver_warning'))
                cmd.extend(["-preset", "p5", "-tune", "hq", "-rc", "cbr_hq", "-b:v", "3500k", "-maxrate", "4000k", "-bufsize", "7000k"] + common_params)
            elif v_enc == "h264_amf": self.log(self.get_translation('amd_amf_warning')); cmd.extend(["-quality", "quality", "-rc", "cbr", "-b:v", "3500k", "-maxrate", "4000k", "-bufsize", "7000k"] + common_params)
            elif v_enc == "h264_qsv": self.log(self.get_translation('intel_qsv_warning')); cmd.extend(["-preset", "fast", "-look_ahead", "1", "-rc_mode", "CBR", "-b:v", "3500k", "-max_bitrate", "4000k", "-bufsize", "7000k"] + common_params)
            else: cmd.extend(["-preset", "veryfast", "-crf", "23", "-maxrate", "3500k", "-bufsize", "7000k"] + common_params) # Fallback to libx264 settings

            a_enc_full = self.audio_handling.get(); a_enc = a_enc_full.split(" ")[0]; cmd.extend(["-c:a", a_enc])
            if a_enc == "aac": cmd.extend(["-b:a", "128k", "-ar", "44100", "-strict", "-2"])
            elif a_enc == "copy": self.log(self.get_translation('copying_audio_info'))
            cmd.extend(["-f", "flv", full_rtmp_url])
            self.log(self.get_translation('executing_command_msg', command=' '.join(cmd)))
            try:
                startupinfo = None; creationflags = 0
                if os.name == 'nt': creationflags = subprocess.CREATE_NO_WINDOW
                self.current_ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8', errors='replace', startupinfo=startupinfo, creationflags=creationflags)
                stderr_lines = []
                for line in iter(self.current_ffmpeg_process.stderr.readline, ''):
                    if not self.streaming_active:
                         self.log(self.get_translation('stop_detected_ffmpeg_output_msg'))
                         if self.current_ffmpeg_process.poll() is None:
                            try: self.current_ffmpeg_process.terminate(); self.current_ffmpeg_process.wait(timeout=1)
                            except Exception: self.current_ffmpeg_process.kill()
                         break
                    line = line.strip()
                    if line: self.log(self.get_translation('ffmpeg_output_log', line=line)); stderr_lines.append(line)
                self.current_ffmpeg_process.stderr.close(); self.current_ffmpeg_process.wait(); return_code = self.current_ffmpeg_process.poll()
                if not self.streaming_active: self.log(self.get_translation('stop_detected_after_file_msg', filename=base_name)); break
                if return_code == 0: self.log(self.get_translation('stream_finished_success_msg', filename=base_name))
                else:
                    if os.name == 'nt' and return_code > 2**31: effective_code = return_code - 2**32
                    else: effective_code = return_code
                    self.log(self.get_translation('ffmpeg_error_exit_msg', code=f"{return_code} ({effective_code})", filename=base_name))
                    error_context = "\n".join(stderr_lines[-10:]); self.log(self.get_translation('ffmpeg_error_context_msg', context=error_context))
                    self.log(self.get_translation('continuing_after_error_warn')); time.sleep(3)
            except FileNotFoundError: self.log(self.get_translation('ffmpeg_command_not_found_fatal', path=self.ffmpeg_path.get())); self.streaming_active = False
            except Exception as e: self.log(self.get_translation('ffmpeg_unexpected_error_fatal', error=e)); import traceback; self.log(traceback.format_exc()); self.streaming_active = False
            finally: self.current_ffmpeg_process = None
            if not self.streaming_active: self.log(self.get_translation('exiting_loop_after_file_msg')); break
            file_index += 1 # ; time.sleep(1)
        if self.streaming_active: self.log(self.get_translation('loop_terminated_unexpectedly_warn')); self.root.after(100, self.reset_controls_after_error)
        self.log(self.get_translation('stream_thread_finished_msg'))


    def reset_controls_after_error(self):
        # (Unchanged logic, calls update_control_states)
        self.streaming_active = False
        self.update_control_states()
        self.log(self.get_translation('buttons_reset_after_error_warn'))

    def on_closing(self):
        # (Unchanged logic, uses translations)
        if self.streaming_active:
            if messagebox.askyesno(self.get_translation('confirm_exit_title'), self.get_translation('confirm_exit_msg')):
                self.stop_streaming()
                self.root.after(500, self.root.destroy)
            # else: return # Don't close implicitly handled
        else:
            self.root.destroy()

# --- Run the application ---
if __name__ == "__main__":
    main_root = tk.Tk()
    app = StreamerApp(main_root)
    main_root.protocol("WM_DELETE_WINDOW", app.on_closing)
    main_root.mainloop()