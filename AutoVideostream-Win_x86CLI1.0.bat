@echo off
chcp 65001
setlocal enabledelayedexpansion

REM 设置窗口标题
title Windows FFmpeg 循环推流脚本

REM --- 用户配置 ---
REM 请确保 ffmpeg.exe 所在的目录已经添加到了系统的 PATH 环境变量中
REM 或者，你可以在下面的命令中直接使用 ffmpeg.exe 的完整路径，例如 C:\path\to\ffmpeg\bin\ffmpeg.exe
set FFMPEG_PATH=ffmpeg
REM --- 用户配置结束 ---

:menu
cls
echo =========================================
echo  Windows FFmpeg 无人值守循环推流脚本
echo =========================================
echo.
echo  重要提示:
echo  1. 请先手动下载 FFmpeg for Windows。
echo  2. 将 ffmpeg.exe 所在的 bin 目录添加到系统的 PATH 环境变量中。
echo     (或者修改脚本中的 FFMPEG_PATH 变量为完整路径)
echo  3. 确保存放视频的文件夹路径和推流地址正确。
echo.
echo =========================================
echo  请选择操作:
echo =========================================
echo  1. 开始无人值守循环推流
echo  2. 停止推流 (结束所有 ffmpeg.exe 进程)
echo  3. 退出
echo =========================================
echo.
set /p choice="请输入数字 (1-3): "

if "%choice%"=="1" goto start_stream
if "%choice%"=="2" goto stop_stream
if "%choice%"=="3" goto exit_script
echo 无效的选择，请重新输入。
pause
goto menu

:start_stream
cls
echo --- 开始推流设置 ---
echo.
:rtmp_input
cls
echo --- 开始推流设置 ---
echo.
set "rtmp="
set /p rtmp="请输入你的推流地址和推流码 (rtmp://...): "

REM === 修正后的验证逻辑 ===
REM 使用字符串截取和比较，避免特殊字符问题
REM 需要启用延迟扩展 (脚本开头已设置 setlocal enabledelayedexpansion)
if /I "!rtmp:~0,7!" == "rtmp://" (
    REM 验证通过
    echo 推流地址: !rtmp!
    echo.
    REM 继续执行脚本的下一部分 (跳转到文件夹输入或其他)
    goto folder_input  REM <--- 确保这里跳转到下一步，例如 :folder_input
) else (
    REM 验证失败
    echo.
    echo  错误: 推流地址必须以 rtmp:// 开头，请重新输入。
    echo.
    pause
    goto rtmp_input
)
REM === 验证逻辑结束 ===

:folder_input
set "folder="
set /p folder="请输入你的视频存放目录 (例如 C:\videos): "
if not exist "%folder%\" (
    echo.
    echo  错误: 目录 "%folder%" 不存在，请重新输入。
    echo.
    goto folder_input
)
REM 检查目录下是否有 MP4 文件 (可选)
dir /b "%folder%\*.mp4" > nul 2>&1
if errorlevel 1 (
    echo.
    echo  警告: 在目录 "%folder%" 中未找到 .mp4 文件。脚本仍会尝试运行。
    echo.
    pause
)
echo 视频目录: %folder%
echo.

:watermark_input
set "watermark_choice="
set /p watermark_choice="是否需要为影片添加水印? (yes/no): "
set "image="
if /i "%watermark_choice%"=="yes" (
    :image_input
    set "image="
    set /p image="请输入你的水印图片存放绝对路径 (例如 C:\images\watermark.png): "
    if not exist "%image%" (
        echo.
        echo  错误: 水印图片 "%image%" 不存在，请重新输入。
        echo.
        goto image_input
    )
    echo 水印图片: %image%
    set add_watermark=1
) else if /i "%watermark_choice%"=="no" (
    echo 不添加水印。
    set add_watermark=0
) else (
    echo 无效输入，请输入 yes 或 no。
    goto watermark_input
)
echo.
echo --- 配置完成，准备开始推流 ---
echo 按任意键开始...
pause > nul

echo.
echo --- 正在循环推流 ---
echo 按 Ctrl+C 或关闭此窗口可停止脚本，或在菜单选择停止推流。
echo.

:stream_loop
REM 进入视频目录
pushd "%folder%"
if errorlevel 1 (
    echo 错误: 无法切换到目录 "%folder%"。
    pause
    goto menu
)

REM 遍历目录下的所有 mp4 文件
for %%F in (*.mp4) do (
    echo --- 开始推流: "%%F" ---
    if "%add_watermark%"=="1" (
        REM 添加水印的命令
        %FFMPEG_PATH% -re -i "%%F" -i "%image%" -filter_complex "overlay=W-w-5:5" -c:v libx264 -preset veryfast -maxrate 2000k -bufsize 4000k -c:a aac -b:a 192k -strict -2 -f flv "%rtmp%"
    ) else (
        REM 不添加水印的命令 (直接复制视频流)
        %FFMPEG_PATH% -re -i "%%F" -c:v copy -c:a aac -b:a 128k -strict -2 -f flv "%rtmp%"
    )
    echo --- "%%F" 推流结束 ---
    echo.
    REM 检查 ffmpeg 是否意外退出，如果需要可以在这里添加错误处理
    REM if errorlevel 1 ( echo FFmpeg 出现错误! & pause & goto menu )
)

REM 返回之前的目录
popd
echo --- 完成一轮视频播放，即将开始下一轮 ---
goto stream_loop

:stop_stream
cls
echo --- 停止推流 ---
echo.
echo 正在尝试结束所有正在运行的 ffmpeg.exe 进程...
taskkill /IM ffmpeg.exe /F
echo.
echo 操作完成。请注意，这会结束系统上 *所有* 的 ffmpeg.exe 进程。
echo.
pause
goto menu

:exit_script
cls
echo 脚本已退出。
exit /b
