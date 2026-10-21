#!/usr/bin/env bash
# Telegram-friendly copy (< 50 MB for a ~60 s reel). Usage: compress_tg.sh IN.mp4 OUT.mp4 [video_kbps]
set -eu
KBPS="${3:-6500}"
ffmpeg -v error -y -i "$1" -c:v libx264 -b:v "${KBPS}k" -maxrate "$((KBPS + 1000))k" -bufsize "$((KBPS * 2))k" \
  -preset medium -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$2"
ls -l "$2"
