#!/bin/bash
# Supports various input formats, transcodes to H.264/AAC for RTMP
# Enhanced error handling, corrected RTMP URL construction, live console stats, improved quality settings
set -e
set -o pipefail # Important for pipelines involving tee

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
FONT_RESET='\033[0m'

# Supported video extensions
VIDEO_EXTENSIONS=("mp4" "mkv" "webm" "avi" "mov" "flv" "ts" "mpg" "mpeg" "wmv")

# Log directory for FFmpeg outputs
LOG_DIR="$HOME/ffmpeg_stream_logs"
mkdir -p "$LOG_DIR"


# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

ffmpeg_check_install() {
    if command_exists ffmpeg; then
        echo -e "${GREEN}FFmpeg is already installed.${FONT_RESET}"
        FFMPEG_PATH=$(command -v ffmpeg)
        echo -e "${GREEN}Current FFmpeg version:${FONT_RESET}"
        "$FFMPEG_PATH" -version | head -n 1
        read -p "$(echo -e "${YELLOW}Do you want to skip FFmpeg installation/update? (yes/no, default: yes): ${FONT_RESET}")" skip_ffmpeg_install
        skip_ffmpeg_install=${skip_ffmpeg_install:-yes} # Default to yes
        if [[ "${skip_ffmpeg_install,,}" == "no" ]]; then
            install_latest_ffmpeg
        else
            echo -e "${GREEN}Skipping FFmpeg installation/update.${FONT_RESET}"
        fi
    else
        echo -e "${YELLOW}FFmpeg is not found.${FONT_RESET}"
        install_latest_ffmpeg
    fi
}

install_latest_ffmpeg() {
    echo -e "${BLUE}Attempting to install/update FFmpeg (latest static build from John Van Sickle)...${FONT_RESET}"
    echo -e "${YELLOW}This will download a pre-compiled static build, which is generally recommended for full codec support.${FONT_RESET}"
    read -p "$(echo -e "${YELLOW}Do you want to proceed with downloading and installing FFmpeg? (yes/no): ${FONT_RESET}")" confirm_install
    if [[ "${confirm_install,,}" != "yes" ]]; then
        echo -e "${RED}FFmpeg installation aborted by user. The script might not work correctly without a capable FFmpeg.${FONT_RESET}"
        return 1
    fi

    local SUDO_CMD=""
    if command_exists sudo; then
        SUDO_CMD="sudo"
    elif [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}sudo command not found and not running as root. Please install sudo or run as root to install FFmpeg.${FONT_RESET}"
        return 1
    fi

    $SUDO_CMD apt update
    $SUDO_CMD apt install -y wget tar xz-utils curl

    ARCH=$(uname -m)
    FFMPEG_STATIC_URL=""
    if [ "$ARCH" = "x86_64" ]; then
        FFMPEG_STATIC_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    elif [ "$ARCH" = "aarch64" ]; then
        FFMPEG_STATIC_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
    else
        echo -e "${RED}Unsupported architecture: $ARCH. Please install FFmpeg manually.${FONT_RESET}"
        return 1
    fi

    echo -e "${BLUE}Downloading FFmpeg from ${FFMPEG_STATIC_URL}...${FONT_RESET}"
    cd /tmp
    if wget -q --show-progress --progress=bar:force:noscroll -O ffmpeg-static.tar.xz "$FFMPEG_STATIC_URL"; then
        echo -e "${GREEN}Download complete. Extracting...${FONT_RESET}"
        rm -rf ffmpeg-*-static
        if tar -xf ffmpeg-static.tar.xz; then
            EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "ffmpeg-*-static" -print -quit)
            if [ -d "$EXTRACTED_DIR" ]; then
                echo -e "${GREEN}Moving ffmpeg and ffprobe to /usr/local/bin/...${FONT_RESET}"
                $SUDO_CMD mv "$EXTRACTED_DIR/ffmpeg" /usr/local/bin/
                $SUDO_CMD mv "$EXTRACTED_DIR/ffprobe" /usr/local/bin/
                $SUDO_CMD chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
                echo -e "${GREEN}FFmpeg installed/updated successfully!${FONT_RESET}"
                ffmpeg -version | head -n 1
            else
                echo -e "${RED}Could not find extracted FFmpeg directory.${FONT_RESET}"; rm -f ffmpeg-static.tar.xz; return 1
            fi
            rm -rf "$EXTRACTED_DIR" ffmpeg-static.tar.xz; cd - > /dev/null
        else
            echo -e "${RED}Failed to extract FFmpeg archive.${FONT_RESET}"; rm -f ffmpeg-static.tar.xz; return 1
        fi
    else
        echo -e "${RED}Failed to download FFmpeg.${FONT_RESET}"; return 1
    fi
}


stream_start() {
    echo -e "${BLUE}Starting stream setup...${FONT_RESET}"

    local rtmp_server_url
    local stream_key
    local full_rtmp_url

    while true; do
        read -p "$(echo -e "${YELLOW}Enter your RTMP Server URL (e.g., rtmp://a.rtmp.youtube.com/live2 or rtmp://live-push.bilivideo.com/live-bvc): ${FONT_RESET}")" rtmp_server_url
        if [[ "$rtmp_server_url" =~ ^rtmp(s)?:// ]]; then
            break
        else
            echo -e "${RED}Invalid RTMP Server URL. It must start with 'rtmp://' or 'rtmps://'. Please try again.${FONT_RESET}"
        fi
    done

    while true; do
        read -p "$(echo -e "${YELLOW}Enter your Stream Key (e.g., for YouTube: xxxx-xxxx-xxxx-xxxx, for Bilibili: ?streamname=live_...&key=...): ${FONT_RESET}")" stream_key
        if [[ -n "$stream_key" ]]; then
            break
        else
            echo -e "${RED}Stream key cannot be empty. Please try again.${FONT_RESET}"
        fi
    done

    if [[ "$stream_key" == \?* ]]; then
        rtmp_server_url_trimmed="${rtmp_server_url%/}"
        full_rtmp_url="${rtmp_server_url_trimmed}${stream_key}"
    else
        rtmp_server_url_trimmed="${rtmp_server_url%/}"
        stream_key_trimmed="${stream_key#\/}"
        full_rtmp_url="${rtmp_server_url_trimmed}/${stream_key_trimmed}"
    fi

    echo -e "${GREEN}Constructed Full RTMP URL: ${FONT_RESET}${BLUE}${full_rtmp_url}${FONT_RESET}"

    if [[ "$stream_key" != \?* && ("$stream_key" == rtmp* || "$stream_key" == http*) ]]; then
        echo -e "${RED}Warning: The Stream Key ('$stream_key') looks like a full URL.${FONT_RESET}"
        echo -e "${YELLOW}This is unusual for stream keys that don't start with '?'. Please double-check.${FONT_RESET}"
    fi

    local video_folder
    while true; do
        read -p "$(echo -e "${YELLOW}Enter your video directory (absolute path, e.g., /opt/videos): ${FONT_RESET}")" video_folder
        if [ -d "$video_folder" ]; then
            echo -e "${GREEN}Video directory set to: $video_folder${FONT_RESET}"; break
        else
            echo -e "${RED}Directory not found: $video_folder. Please enter a valid absolute path.${FONT_RESET}"
        fi
    done

    echo -e "${BLUE}Starting infinite loop for streaming... Press Ctrl+C to stop this script (if not in screen/tmux).${FONT_RESET}"
    echo -e "${YELLOW}FFmpeg logs (full output) will be saved in: ${LOG_DIR}${FONT_RESET}"
    echo -e "${YELLOW}FFmpeg live stats (stderr) will be shown on this console.${FONT_RESET}"


    while true; do
        echo -e "${GREEN}Searching for video files in '$video_folder' and shuffling...${FONT_RESET}"
        
        local find_options_str=""
        for ext_idx in "${!VIDEO_EXTENSIONS[@]}"; do
            if [ "$ext_idx" -eq 0 ]; then
                find_options_str="-iname \"*.${VIDEO_EXTENSIONS[$ext_idx]}\""
            else
                find_options_str="$find_options_str -o -iname \"*.${VIDEO_EXTENSIONS[$ext_idx]}\""
            fi
        done

        mapfile -t video_files < <(eval "find \"$video_folder\" -type f \( $find_options_str \) -print0" | shuf -z | xargs -0 -r printf "%s\n")
        
        if [ ${#video_files[@]} -eq 0 ]; then
            echo -e "${RED}No video files found in '$video_folder'. Waiting 30s...${FONT_RESET}"; sleep 30; continue
        fi

        echo -e "${GREEN}Found ${#video_files[@]} video files. Starting playback cycle.${FONT_RESET}"

        for video_file in "${video_files[@]}"; do
            local safe_video_filename; safe_video_filename=$(basename "$video_file" | tr -cd '[:alnum:]._-')
            local ffmpeg_logfile="${LOG_DIR}/ffmpeg_${safe_video_filename}_$(date +%Y%m%d-%H%M%S).log"

            echo -e "${BLUE}------------------------------------------------------------------${FONT_RESET}"
            echo -e "${GREEN}Streaming video: $video_file${FONT_RESET}"
            echo -e "${GREEN}Target RTMP URL: $full_rtmp_url${FONT_RESET}"
            echo -e "${YELLOW}FFmpeg full output (stdout & stderr) logged to: ${ffmpeg_logfile}${FONT_RESET}"
            echo -e "${YELLOW}FFmpeg live stats/errors (stderr) will appear below:${FONT_RESET}"
            
            # -preset fast：ultrafast / superfast / fast / medium/ slow / veryslow
            # -maxrate 5000k, -bufsize 7500k: Increased bitrate.
            # FFmpeg typically sends stats to stderr by default if stderr is a TTY. tee pipes this.
            ffmpeg_cmd=(
                ffmpeg -hide_banner -stats_period 2 \
                -re -nostdin \
                -analyzeduration 50M -probesize 50M \
                -i "$video_file" \
                -c:v libx264 -preset slow -tune zerolatency -pix_fmt yuv420p \
                -maxrate 5000k -bufsize 7500k -g 120 -keyint_min 120 -sc_threshold 0 \
                -c:a aac -b:a 128k -ar 44100 \
                -threads 0 \
                -f flv \
                -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3 \
                "$full_rtmp_url"
            )
            
            echo -e "${BLUE}FFmpeg command (approximate):${FONT_RESET} ${YELLOW}${ffmpeg_cmd[*]}${FONT_RESET}"
            echo -e "${BLUE}------------------------------------------------------------------${FONT_RESET}"

            local ffmpeg_execution_failed=false
            local ffmpeg_exit_code=0

            # Execute FFmpeg.
            # stderr (progress, errors) is tee'd to logfile AND this script's stderr (console).
            # stdout (rarely used by ffmpeg for messages) goes only to logfile.
            # The subshell `()` ensures we capture the exit code of ffmpeg.
            if ! (("${ffmpeg_cmd[@]}" 2> >(tee -a "$ffmpeg_logfile" >&2)) 1>> "$ffmpeg_logfile"); then
                ffmpeg_exit_code=$? # Capture actual exit code of ffmpeg
                ffmpeg_execution_failed=true
            else
                ffmpeg_exit_code=0 # FFmpeg command itself exited 0
            fi

            # After FFmpeg finishes (or crashes), print a separator for clarity on console
            echo -e "${BLUE}---------------------- FFmpeg process ended ----------------------${FONT_RESET}"

            local ffmpeg_failed_semantically=false
            if $ffmpeg_execution_failed; then
                ffmpeg_failed_semantically=true
                echo -e "${RED}FFmpeg for '$video_file' FAILED (non-zero exit code: $ffmpeg_exit_code).${FONT_RESET}"
            else # FFmpeg exited with 0, check log for errors just in case
                if grep -Eqi "Error opening output|Input/output error|Conversion failed|Could not write header|Unknown error occurred|Invalid argument|Connection refused|Operation not permitted|Segfault|Segmentation fault" "$ffmpeg_logfile"; then
                    ffmpeg_failed_semantically=true
                    echo -e "${RED}FFmpeg for '$video_file' exited with 0, BUT fatal errors found in log! Treating as FAILURE.${FONT_RESET}"
                fi
            fi

            if $ffmpeg_failed_semantically; then
                echo -e "${RED}Please check the full log for details: ${ffmpeg_logfile}${FONT_RESET}"
                echo -e "${YELLOW}Last 15 lines of the log:${FONT_RESET}"
                tail -n 15 "$ffmpeg_logfile"
                echo -e "${YELLOW}Skipping to next video in 0 seconds...${FONT_RESET}"
                sleep 0
            else
                echo -e "${GREEN}Finished streaming '$video_file' (FFmpeg process reported success).${FONT_RESET}"
                # rm -f "$ffmpeg_logfile" # Uncomment to remove successful logs
            fi
            sleep 0 # Brief pause before next video
        done
        echo -e "${YELLOW}Cycle complete. Re-shuffling and starting over...${FONT_RESET}"; sleep 0
    done
}

stream_stop() {
    echo -e "${YELLOW}Attempting to stop FFmpeg processes...${FONT_RESET}"
    local killed_processes=false
    # More specific pattern matching our ffmpeg command structure
    if pgrep -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://" > /dev/null; then
        echo -e "${BLUE}Found FFmpeg processes matching stream pattern. Attempting graceful stop (SIGTERM)...${FONT_RESET}"
        pkill -SIGTERM -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://" && sleep 2
        if pgrep -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://" > /dev/null; then
            echo -e "${YELLOW}Processes still running. Attempting forceful stop (SIGKILL)...${FONT_RESET}"
            pkill -SIGKILL -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://"
        fi
        echo -e "${GREEN}Targeted FFmpeg processes should be stopped.${FONT_RESET}"
        killed_processes=true
    fi

    if ! $killed_processes; then
        if pgrep ffmpeg > /dev/null; then
            echo -e "${YELLOW}No specific stream processes found or they resisted. Trying 'killall ffmpeg'...${FONT_RESET}"
            if killall ffmpeg > /dev/null 2>&1; then
                 echo -e "${GREEN}All FFmpeg processes stopped via killall.${FONT_RESET}"
            else
                 echo -e "${RED}killall ffmpeg failed or no general ffmpeg processes found.${FONT_RESET}"
            fi
        else
            echo -e "${GREEN}No FFmpeg processes seem to be running.${FONT_RESET}"
        fi
    fi
    echo -e "${YELLOW}If using screen/tmux, manually terminate the session (e.g., 'screen -S stream_session -X quit').${FONT_RESET}"
}

view_logs() {
    echo -e "${BLUE}Recent FFmpeg Logs:${FONT_RESET}"
    if [ -d "$LOG_DIR" ] && [ "$(ls -A $LOG_DIR)" ]; then
        echo -e "${YELLOW}Last 10 log files in ${LOG_DIR} (newest first):${FONT_RESET}"
        ls -lt "$LOG_DIR" | grep "ffmpeg_" | head -n 10
        
        error_logs_found=false
        echo -e "\n${YELLOW}Searching for logs with errors...${FONT_RESET}"
        potential_error_files=$(find "$LOG_DIR" -type f -name "ffmpeg_*.log" -print0 | xargs -0 -r grep -lEi 'FAIL|unable to|error|segmentation fault|crash|ailed|invalid|refused|denied|permitted')
        if [ -n "$potential_error_files" ]; then
            echo -e "${GREEN}Potential error logs (most recent first, up to 5):${FONT_RESET}"
            echo "$potential_error_files" | xargs -r ls -t | head -n 5
            error_logs_found=true
        else
            echo -e "${GREEN}No logs with common error keywords found in the last search.${FONT_RESET}"
        fi
        
        echo -e "\n${YELLOW}To view a specific log: cat ${LOG_DIR}/<filename> or less ${LOG_DIR}/<filename>${FONT_RESET}"
        if $error_logs_found; then
            read -p "$(echo -e "${YELLOW}Enter a log filename from above to view its last 20 lines (or Enter to skip): ${FONT_RESET}")" log_to_view
            if [ -n "$log_to_view" ] && [ -f "$LOG_DIR/$log_to_view" ]; then
                tail -n 20 "$LOG_DIR/$log_to_view"
            elif [ -n "$log_to_view" ]; then
                echo -e "${RED}Log file '$log_to_view' not found in $LOG_DIR.${FONT_RESET}"
            fi
        fi
    else
        echo -e "${YELLOW}No log files found in ${LOG_DIR}.${FONT_RESET}"
    fi
}

main_menu() {
    clear
    echo -e "${YELLOW}Ubuntu FFmpeg Unattended Loop Streamer (Upgraded v4)${FONT_RESET}"
    echo -e "${RED}IMPORTANT: For long-running streams, run this script inside a 'screen' or 'tmux' session!${FONT_RESET}"
    echo -e "${GREEN}Example: screen -S stream_session bash $(basename "$0")${FONT_RESET}"
    echo -e "${GREEN}FFmpeg logs are stored in: ${LOG_DIR}${FONT_RESET}"
    echo -e "-----------------------------------------------------"
    echo -e "${BLUE}1. Check/Install/Update FFmpeg${FONT_RESET}"
    echo -e "${BLUE}2. Start Unattended Loop Streaming${FONT_RESET}"
    echo -e "${BLUE}3. Stop Streaming (kills FFmpeg processes)${FONT_RESET}"
    echo -e "${BLUE}4. View FFmpeg Logs${FONT_RESET}"
    echo -e "${BLUE}5. Exit${FONT_RESET}"
    echo -e "-----------------------------------------------------"
    read -p "$(echo -e "${YELLOW}Enter your choice (1-5): ${FONT_RESET}")" choice

    case "$choice" in
        1) ffmpeg_check_install ;;
        2)
            if ! command_exists ffmpeg; then
                echo -e "${RED}FFmpeg not found. Install via option 1 first.${FONT_RESET}"
            else
                echo -e "${YELLOW}Starting stream. To stop, use Option 3 from this menu (in another terminal if needed), or Ctrl+C if this script is not in screen/tmux.${FONT_RESET}"
                stream_start
            fi
            ;;
        3) stream_stop ;;
        4) view_logs ;;
        5) echo -e "${GREEN}Exiting.${FONT_RESET}"; exit 0 ;;
        *) echo -e "${RED}Invalid choice (1-5).${FONT_RESET}" ;;
    esac
    echo ""; read -p "Press Enter for main menu..."
    main_menu
}

# Run the main menu
main_menu
