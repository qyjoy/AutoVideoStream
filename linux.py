#!/usr/bin/env python3
import os
import sys
import glob
import time
import argparse
import subprocess
import signal
import logging

# 全局变量用于信号控制
stop_requested = False
switch_requested = False
current_ffmpeg_process = None

VIDEO_EXTENSIONS = ["*.webm", "*.mp4", "*.mkv", "*.mov", "*.avi", "*.flv"]

def parse_args():
    parser = argparse.ArgumentParser(
        description="AutoVideoStreamerCLI: 目录循环推流，无人值守 Linux CLI 版本"
    )
    parser.add_argument('--ffmpeg', default='ffmpeg', help='ffmpeg路径（默认在PATH）')
    parser.add_argument('--rtmp', required=True, help='RTMP推流基础URL（如rtmp://...）')
    parser.add_argument('--key', required=True, help='推流密钥')
    parser.add_argument('--video-dir', required=True, help='视频文件目录')
    parser.add_argument('--encoder', default='libx264', choices=['libx264', 'h264_nvenc', 'h264_amf', 'h264_qsv'],
                        help='视频编码器')
    parser.add_argument('--audio', default='aac', choices=['aac', 'copy'], help='音频处理方式')
    parser.add_argument('--watermark', default=None, help='水印图片路径（可选）')
    parser.add_argument('--logfile', default='streamer.log', help='日志文件路径')
    parser.add_argument('--maxrate', default='3500k', help='视频最大码率')
    parser.add_argument('--bufsize', default='7000k', help='视频缓冲区大小')
    parser.add_argument('--crf', default='23', help='libx264质量因子')
    parser.add_argument('--loop-interval', type=int, default=3, help='推流文件出错后，重试间隔（秒）')
    return parser.parse_args()

def setup_logging(logfile):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(logfile, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def signal_handler(signum, frame):
    global stop_requested, switch_requested, current_ffmpeg_process
    if signum in (signal.SIGINT, signal.SIGTERM):
        logging.info("收到退出信号，准备优雅停止。")
        stop_requested = True
        # 尝试终止ffmpeg
        if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
            current_ffmpeg_process.terminate()
    elif signum == signal.SIGHUP:
        logging.info("收到SIGHUP，切换下一个视频。")
        switch_requested = True
        if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
            current_ffmpeg_process.terminate()

def find_videos(directory):
    files = []
    for ext in VIDEO_EXTENSIONS:
        files.extend(glob.glob(os.path.join(directory, ext)))
    return sorted(files)

def build_ffmpeg_cmd(args, video_file):
    cmd = [args.ffmpeg, '-re', '-i', video_file]
    filter_complex = []
    if args.watermark:
        cmd += ['-i', args.watermark]
        filter_complex.append('[0:v][1:v]overlay=main_w-overlay_w-10:10')
    if filter_complex:
        cmd += ['-filter_complex', ';'.join(filter_complex)]
    cmd += ['-c:v', args.encoder]
    cmd += ['-g', '60', '-pix_fmt', 'yuv420p', '-max_muxing_queue_size', '1024']
    if args.encoder == 'libx264':
        cmd += ['-preset', 'veryfast', '-crf', str(args.crf), '-maxrate', args.maxrate, '-bufsize', args.bufsize]
    elif args.encoder == 'h264_nvenc':
        cmd += ['-preset', 'p5', '-tune', 'hq', '-rc', 'cbr', '-b:v', args.maxrate, '-maxrate', '4000k', '-bufsize', args.bufsize]
    elif args.encoder == 'h264_amf':
        cmd += ['-quality', 'balanced', '-rc', 'cbr', '-b:v', args.maxrate, '-maxrate', '4000k', '-bufsize', args.bufsize]
    elif args.encoder == 'h264_qsv':
        cmd += ['-preset', 'medium', '-look_ahead', '1', '-rc_mode', 'CBR', '-b:v', args.maxrate, '-max_bitrate', '4000k', '-bufsize', args.bufsize]
    # 音频
    cmd += ['-c:a', args.audio]
    if args.audio == 'aac':
        cmd += ['-b:a', '128k', '-ar', '44100']
    cmd += ['-f', 'flv', f"{args.rtmp.rstrip('/')}/{args.key}"]
    return cmd

def main():
    global stop_requested, switch_requested, current_ffmpeg_process
    args = parse_args()
    setup_logging(args.logfile)

    # 注册信号
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)

    logging.info("推流服务启动。")
    logging.info(f"视频目录: {args.video_dir}")
    file_list = find_videos(args.video_dir)
    if not file_list:
        logging.error("没有找到任何视频文件，程序退出。")
        sys.exit(1)

    file_index = 0
    while not stop_requested:
        if file_index >= len(file_list):
            file_index = 0
            logging.info("一轮播放结束，开始下一轮。")
        video_file = file_list[file_index]
        logging.info(f"开始推流: {os.path.basename(video_file)}")
        cmd = build_ffmpeg_cmd(args, video_file)
        logging.info(f"FFmpeg命令: {' '.join(cmd)}")
        try:
            current_ffmpeg_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8'
            )
            # 实时输出日志
            for line in current_ffmpeg_process.stdout:
                if line:
                    logging.info(line.strip())
                if stop_requested or switch_requested:
                    break
            current_ffmpeg_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logging.warning("FFmpeg进程超时，强制终止。")
            current_ffmpeg_process.kill()
        except Exception as e:
            logging.error(f"推流异常: {e}")
        finally:
            current_ffmpeg_process = None

        if stop_requested:
            logging.info("检测到退出信号，停止推流。")
            break
        elif switch_requested:
            logging.info("检测到切换信号，准备切下一个视频。")
            switch_requested = False
            file_index = (file_index + 1) % len(file_list)
            continue
        else:
            file_index += 1
        time.sleep(args.loop_interval)

    logging.info("推流服务退出。")

if __name__ == '__main__':
    main()
