# AutoVideoStream Powered By ffmpeg
Video Auto Stream 24/7 ffmpeg Screenshots
![image](https://github.com/user-attachments/assets/40b80d5c-cb67-4916-aa78-5ea65b207943)

# VideoToStream24HForWindows

## 目录

- [中文文档](#中文文档)
  - [功能特性](#功能特性)
  - [使用指南](#使用指南)
  - [系统要求](#系统要求)
- [English Documentation](#english-documentation)
  - [Features](#features)
  - [Quick Start](#quick-start)
  - [Requirements](#requirements)

---

## 中文文档

### <font size="5">✨ 功能特性</font>

#### <font size="4"> 核心功能</font>

- **24/7循环推流**
  - `√` 自动检测文件夹内视频文件
  - `√` 无缝循环播放
  - `√` 支持MP4/MKV/MOV/AVI格式

#### <font size="4"> 编码选项</font>

| 编码类型   | 支持方案                |
| -------- | ----------------------- |
| 视频编码   | libx264 / NVENC / AMF / QSV |
| 音频处理   | AAC重编码 / 直接流复制      |

#### <font size="4"> 界面特色</font>

```diff
+ 5种预设主题配色
+ 实时日志监控窗口
+ 中英文双语切换

一个基于FFmpeg的24/7循环推流GUI工具，支持：
自动循环播放文件夹中的视频
多种编码器选择（CPU/NVIDIA/AMD/Intel）
水印添加功能
多语言支持（简体中文/英文）
多种主题切换
实时日志输出
功能特点
 推流设置

支持RTMP推流地址和推流码配置
可自定义FFmpeg路径（自动检测系统PATH）
 视频处理

支持多种视频格式（MP4/MKV/MOV/AVI）
可添加静态水印图片
自动循环播放文件夹内视频
 编码选项

视频编码器：
libx264 (CPU)
h264_nvenc (NVIDIA)
h264_amf (AMD)
h264_qsv (Intel)
音频处理：
AAC重新编码
直接复制音频流
 界面特性

多语言支持（中英文切换）
5种预设主题（默认/夜间/白色/蓝调/炫彩）
实时日志窗口
响应式布局
使用说明
 基本使用

设置FFmpeg路径（或使用系统PATH）
输入RTMP地址和推流码
选择视频文件夹
点击"开始推流"
 高级选项

勾选"添加水印"可设置水印图片
根据硬件选择最佳编码器
通过菜单切换语言和主题
 注意事项

使用硬件编码器需确保驱动已正确安装
水印图片需为常见格式（PNG/JPG等）
停止推流可能需要几秒时间完成
系统要求
Windows/Linux/macOS（需Python环境）
FFmpeg（已安装或指定路径）
Python 3.6+
推荐硬件：
支持硬件编码的显卡（可选）
4GB以上内存（高清视频推流）

常见问题
Q: 推流失败怎么办？
A: 检查日志中的FFmpeg错误信息，常见原因：

FFmpeg路径不正确
RTMP地址格式错误
视频文件损坏
Q: 如何添加新的主题？
A: 修改代码中的themes字典，添加新的配色方案

Q: 支持直播平台有哪些？
A: 支持所有标准RTMP协议平台（如Twitch/YouTube/B站等）

## English Documentation

A FFmpeg-based 24/7 streaming GUI tool with:

- Automatic video loop playback
- Multiple encoder options (CPU/NVIDIA/AMD/Intel)
- Watermark support
- Multi-language (English/Chinese)
- Theme customization
- Real-time logging

### Features

#### Streaming Setup

- RTMP URL and stream key configuration
- Custom FFmpeg path (auto-detects system PATH)

#### Video Processing

- Supports multiple formats (MP4/MKV/MOV/AVI)
- Static watermark overlay
- Automatic folder looping

#### Encoding Options

- Video encoders:
  - libx264 (CPU)
  - h264_nvenc (NVIDIA)
  - h264_amf (AMD)
  - h264_qsv (Intel)
- Audio handling:
  - AAC re-encode
  - Direct stream copy

#### UI Features

- Bilingual support (EN/CN)
- 5 preset themes (Default/Night/White/Blue/Vibrant)
- Real-time log window
- Responsive layout

### Quick Start

#### Basic Usage

- Set FFmpeg path (or use system PATH)
- Enter RTMP URL and stream key
- Select video folder
- Click "Start Streaming"

#### Advanced Options

- Enable "Add Watermark" for image overlay
- Select optimal encoder for your hardware
- Change language/theme via menu

#### Notes

- Hardware encoders require proper drivers
- Watermark should be common formats (PNG/JPG)
- Stopping stream may take few seconds

### Requirements

- Windows/Linux/macOS (Python required)
- FFmpeg (installed or specified path)
- Python 3.6+
- Recommended:
  - Hardware-accelerated GPU (optional)
  - 4GB+ RAM (for HD streaming)

### FAQ

- Q: Streaming fails?
  - A: Check FFmpeg errors in log, common causes:
    - Incorrect FFmpeg path
    - Invalid RTMP URL format
    - Corrupted video files
- Q: How to add new themes?
  - A: Modify the themes dictionary in code
- Q: Supported platforms?
  - A: Works with all standard RTMP services (Twitch/YouTube/Bilibili etc.)

### Author

QyJoy (V3.0)
