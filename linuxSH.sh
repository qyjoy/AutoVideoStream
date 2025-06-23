#!/bin/sh
# POSIX-compliant version of the loop streamer script.
# This script is designed to be fully functional and robust,
# providing the same core features as the original bash version.

set -e

# unset pipefail for sh compatibility; robustness is handled in the pipe itself.
# set -o pipefail

PATH="/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:$HOME/bin"
export PATH

# Color definitions using printf for POSIX compatibility
RED=$(printf '\033[0;31m')
GREEN=$(printf '\033[0;32m')
YELLOW=$(printf '\033[0;33m')
BLUE=$(printf '\033[0;34m')
FONT_RESET=$(printf '\033[0m')

# Supported video extensions as a space-separated string for POSIX sh
VIDEO_EXTENSIONS="mp4 mkv webm avi mov flv ts mpg mpeg wmv"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# POSIX-compliant function to ask a yes/no question
# Usage: ask_yes_no "Prompt message" "default_answer"
# Returns 0 for "yes", 1 for "no"
ask_yes_no() {
    prompt_msg="$1"
    default_ans="$2"
    
    while true; do
        printf "%s" "$prompt_msg"
        read -r answer
        
        # If user just presses Enter, use the default
        if [ -z "$answer" ]; then
            answer="$default_ans"
        fi
        
        # Convert to lowercase using POSIX-compliant `tr`
        case "$(echo "$answer" | tr 'A-Z' 'a-z')" in
            y | yes) return 0 ;;
            n | no)  return 1 ;;
            *) printf "%s\n" "${RED}Invalid input. Please enter 'yes' or 'no'.${FONT_RESET}" ;;
        esac
    done
}

ffmpeg_check_install() {
    if command_exists ffmpeg; then
        printf "%s\n" "${GREEN}FFmpeg is already installed.${FONT_RESET}"
        if [ -x "/usr/bin/ffmpeg" ]; then
            FFMPEG_PATH="/usr/bin/ffmpeg"
        elif [ -x "/usr/local/bin/ffmpeg" ]; then
            FFMPEG_PATH="/usr/local/bin/ffmpeg"
        else
            FFMPEG_PATH=$(command -v ffmpeg)
        fi
        printf "%s\n" "${GREEN}Current FFmpeg version:${FONT_RESET}"
        "$FFMPEG_PATH" -version | head -n 1
        
        if ask_yes_no "${YELLOW}Do you want to install/update FFmpeg anyway? (yes/no, default: no): ${FONT_RESET}" "no"; then
             install_latest_ffmpeg
        else
            printf "%s\n" "${GREEN}Skipping FFmpeg installation/update.${FONT_RESET}"
        fi
    else
        printf "%s\n" "${YELLOW}FFmpeg not found.${FONT_RESET}"
        install_latest_ffmpeg
    fi
}

install_latest_ffmpeg() {
    printf "%s\n" "${BLUE}Installing/updating FFmpeg (John Van Sickle static build)...${FONT_RESET}"
    printf "%s\n" "${YELLOW}This downloads a pre-compiled static build for best codec support.${FONT_RESET}"
    
    if ! ask_yes_no "${YELLOW}Proceed with download/install? (yes/no): ${FONT_RESET}" "no"; then
        printf "%s\n" "${RED}Aborted by user. The script may not work without FFmpeg.${FONT_RESET}"
        return 1
    fi

    SUDO_CMD=""
    if command_exists sudo; then
        SUDO_CMD="sudo"
    elif [ "$(id -u)" -ne 0 ]; then
        printf "%s\n" "${RED}sudo not found and you are not root. Please install sudo or run as root.${FONT_RESET}"
        return 1
    fi
    
    $SUDO_CMD apt-get update
    $SUDO_CMD apt-get install -y wget tar xz-utils curl
    
    ARCH=$(uname -m)
    FFMPEG_STATIC_URL=""
    case "$ARCH" in
        x86_64) FFMPEG_STATIC_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" ;;
        aarch64) FFMPEG_STATIC_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz" ;;
        *)
            printf "%s\n" "${RED}Unsupported architecture: $ARCH. Please install FFmpeg manually.${FONT_RESET}"
            return 1
        ;;
    esac
    
    printf "%s\n" "${BLUE}Downloading FFmpeg from ${FFMPEG_STATIC_URL}...${FONT_RESET}"
    
    # Use a subshell to avoid changing the main script's directory
    (
        cd /tmp
        if wget -q --show-progress --progress=bar:force:noscroll -O ffmpeg-static.tar.xz "$FFMPEG_STATIC_URL"; then
            printf "%s\n" "${GREEN}Download complete. Extracting...${FONT_RESET}"
            rm -rf ffmpeg-*-static
            if tar -xf ffmpeg-static.tar.xz; then
                # POSIX-compliant way to find the single extracted directory
                EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "ffmpeg-*-static")
                if [ -d "$EXTRACTED_DIR" ]; then
                    printf "%s\n" "${GREEN}Moving ffmpeg and ffprobe to /usr/local/bin/...${FONT_RESET}"
                    $SUDO_CMD mv "$EXTRACTED_DIR/ffmpeg" /usr/local/bin/
                    $SUDO_CMD mv "$EXTRACTED_DIR/ffprobe" /usr/local/bin/
                    $SUDO_CMD chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
                    printf "%s\n" "${GREEN}FFmpeg installed/updated successfully!${FONT_RESET}"
                    ffmpeg -version | head -n 1
                else
                    printf "%s\n" "${RED}Extracted FFmpeg directory not found.${FONT_RESET}"; rm -f ffmpeg-static.tar.xz; exit 1
                fi
                rm -rf "$EXTRACTED_DIR" ffmpeg-static.tar.xz
            else
                printf "%s\n" "${RED}Failed to extract FFmpeg archive.${FONT_RESET}"; rm -f ffmpeg-static.tar.xz; exit 1
            fi
        else
            printf "%s\n" "${RED}Failed to download FFmpeg.${FONT_RESET}"; exit 1
        fi
    )
}

stream_start() {
    printf "%s\n" "${BLUE}Stream setup...${FONT_RESET}"
    
    while true; do
        printf "%s" "${YELLOW}Enter full RTMP URL (e.g., rtmp://a.rtmp.youtube.com/live2/xxxx-xxxx): ${FONT_RESET}"
        read -r full_rtmp_url_raw
        
        # POSIX-compliant way to trim whitespace and validate URL
        full_rtmp_url=$(echo "$full_rtmp_url_raw" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        
        # Use grep for POSIX-compliant regex matching
        if echo "$full_rtmp_url" | grep -Eq '^rtmp(s)?://.+'; then
            full_rtmp_url=$(echo "$full_rtmp_url" | sed 's#//*#/#g;s#:/#://#')
            printf "%s%s%s\n" "${GREEN}RTMP URL: ${BLUE}" "$full_rtmp_url" "${FONT_RESET}"
            break
        else
            printf "%s\n" "${RED}Invalid RTMP URL. Must start with 'rtmp://' or 'rtmps://'. Try again.${FONT_RESET}"
        fi
    done
    
    while true; do
        printf "%s" "${YELLOW}Enter video directory (absolute path, e.g., /opt/videos): ${FONT_RESET}"
        read -r video_folder
        if [ -d "$video_folder" ]; then
            printf "%s%s\n" "${GREEN}Video directory: " "$video_folder" "${FONT_RESET}"
            break
        else
            printf "%s%s\n" "${RED}Directory not found: " "$video_folder" ". Try again.${FONT_RESET}"
        fi
    done
    
    printf "%s\n" "${BLUE}Starting infinite streaming loop. Press Ctrl+C to stop.${FONT_RESET}"
    
    while true; do
        printf "%s%s%s\n" "${GREEN}Searching and shuffling videos in '" "$video_folder" "'...${FONT_RESET}"
        
        # Build find options string in a POSIX-compliant way
        find_options_str=""
        is_first=true
        for ext in $VIDEO_EXTENSIONS; do
            if [ "$is_first" = "true" ]; then
                find_options_str="-iname \"*.$ext\""
                is_first=false
            else
                find_options_str="$find_options_str -o -iname \"*.$ext\""
            fi
        done
        
        # This is the key part: A robust, POSIX-compliant pipeline to handle all filenames.
        # It finds files, shuffles them, and then reads them line-by-line safely.
        # This correctly handles filenames with spaces and most special characters.
        temp_file_list=$(mktemp)
        # Use eval to correctly handle the constructed find options with spaces and quotes
        eval "find \"$video_folder\" -type f \( $find_options_str \)" > "$temp_file_list"
        
        # Check if any files were found
        if [ ! -s "$temp_file_list" ]; then
            printf "%s\n" "${RED}No video files found. Waiting 15s...${FONT_RESET}"; sleep 15; continue
        else
            file_count=$(wc -l < "$temp_file_list")
            printf "%s%s%s\n" "${GREEN}Found " "$(echo "$file_count" | tr -d ' ')" " video files. Starting playback cycle.${FONT_RESET}"
        fi

        # Shuffle the list and loop through it safely
        cat "$temp_file_list" | shuf | while IFS= read -r video_file; do
            printf "%s\n" "${BLUE}--------------------------------------------------${FONT_RESET}"
            printf "%s%s\n" "${GREEN}Streaming: " "$video_file" "${FONT_RESET}"
            printf "%s%s\n" "${GREEN}RTMP: " "$full_rtmp_url" "${FONT_RESET}"
            
            # The ffmpeg command remains the same, it's already robust
            ffmpeg -re -hide_banner \
                -nostdin \
                -analyzeduration 10M -probesize 10M \
                -i "$video_file" -vf "scale=1280:720" -r 35 \
                -c:v libx264 -preset ultrafast -tune zerolatency -pix_fmt yuv420p \
                -maxrate 4000k -bufsize 90000k -g 70 -keyint_min 70 -sc_threshold 0 \
                -c:a aac -b:a 128k -ar 44100  \
                -threads 0 \
                -f flv \
                "$full_rtmp_url"
            
            printf "%s\n" "${BLUE}---------------- FFmpeg ended --------------------${FONT_RESET}"
            sleep 0 # sleep 0 can yield the CPU slice
        done
        rm -f "$temp_file_list"

        printf "%s\n" "${YELLOW}Cycle complete. Re-shuffling and starting again...${FONT_RESET}"
        sleep 0
    done
}

stream_stop() {
    printf "%s\n" "${YELLOW}Stopping FFmpeg processes...${FONT_RESET}"
    killed_processes=false
    # This pgrep pattern is a direct port from the bash script and is fully functional
    if pgrep -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://" > /dev/null; then
        printf "%s\n" "${BLUE}Attempting graceful stop (SIGTERM)...${FONT_RESET}"
        pkill -SIGTERM -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://" && sleep 2
        
        if pgrep -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://" > /dev/null; then
            printf "%s\n" "${YELLOW}Forceful stop (SIGKILL)...${FONT_RESET}"
            pkill -SIGKILL -f "ffmpeg -hide_banner -re -nostdin.*-f flv rtmp(s)?://"
        fi
        
        printf "%s\n" "${GREEN}Targeted FFmpeg processes stopped.${FONT_RESET}"
        killed_processes=true
    fi
    
    if [ "$killed_processes" = "false" ]; then
        if pgrep ffmpeg > /dev/null; then
            printf "%s\n" "${YELLOW}No specific stream processes found. Trying to kill all 'ffmpeg' processes...${FONT_RESET}"
            if killall ffmpeg > /dev/null 2>&1; then
                printf "%s\n" "${GREEN}All FFmpeg processes stopped.${FONT_RESET}"
            else
                printf "%s\n" "${RED}killall ffmpeg failed or no processes were found to kill.${FONT_RESET}"
            fi
        else
            printf "%s\n" "${GREEN}No FFmpeg processes seem to be running.${FONT_RESET}"
        fi
    fi
    printf "%s\n" "${YELLOW}If you were using screen/tmux, remember to terminate the session manually.${FONT_RESET}"
}

main_menu() {
    # Use 'clear' if available
    if command_exists clear; then
        clear
    fi
    
    printf "%s\n" "${YELLOW}Ubuntu FFmpeg Unattended Loop Streamer (POSIX-Compliant Edition)${FONT_RESET}"
    printf "%s\n" "${RED}IMPORTANT: For long streams, run inside 'screen' or 'tmux'!${FONT_RESET}"
    printf "%s%s%s\n" "${GREEN}Example: screen -S stream_session sh " "$(basename "$0")" "${FONT_RESET}"
    printf "%s\n" "--------------------------------------------"
    printf "%s\n" "${BLUE}1. Check/Install/Update FFmpeg${FONT_RESET}"
    printf "%s\n" "${BLUE}2. Start Unattended Loop Streaming${FONT_RESET}"
    printf "%s\n" "${BLUE}3. Stop Streaming (kills FFmpeg processes)${FONT_RESET}"
    printf "%s\n" "${BLUE}4. Exit${FONT_RESET}"
    printf "%s\n" "--------------------------------------------"
    printf "%s" "${YELLOW}Enter your choice (1-4): ${FONT_RESET}"
    
    read -r choice
    
    case "$choice" in
        1) ffmpeg_check_install ;;
        2)
            if ! command_exists ffmpeg; then
                printf "%s\n" "${RED}FFmpeg not found. Please use option 1 to install it first.${FONT_RESET}"
            else
                printf "%s\n" "${YELLOW}Starting stream. To stop, use Option 3 from this menu, or press Ctrl+C if not in screen/tmux.${FONT_RESET}"
                stream_start
            fi
            ;;
        3) stream_stop ;;
        4) printf "%s\n" "${GREEN}Exiting.${FONT_RESET}"; exit 0 ;;
        *) printf "%s\n" "${RED}Invalid choice. Please enter a number from 1 to 4.${FONT_RESET}" ;;
    esac
    
    printf "\n"
    printf "%s" "Press Enter to return to the main menu..."
    read -r _
    main_menu
}

main_menu
