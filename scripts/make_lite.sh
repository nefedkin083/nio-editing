#!/usr/bin/env bash
# 480p / 15 fps proxies of every clip in raw/ -> lite/ (for Gemini; small and fast).
# Horizontal clips are skipped by default (reels are vertical). Pass --keep-horizontal to keep them.
set -u
KEEP_H=0; [ "${1:-}" = "--keep-horizontal" ] && KEEP_H=1
mkdir -p lite
export KEEP_H
find raw -maxdepth 1 -type f \( -iname '*.mov' -o -iname '*.mp4' -o -iname '*.m4v' -o -iname '*.mkv' -o -iname '*.webm' \) -print0 |
xargs -0 -P 3 -I{} bash -c '
f="{}"; name=$(basename "${f%.*}"); out="lite/${name}.mp4"
[ -f "$out" ] && exit 0
ffmpeg -hide_banner -loglevel error -nostdin -y -i "$f" -map 0:v:0 -map "0:a:0?" \
  -vf "scale=-2:480,fps=15" -c:v libx264 -crf 32 -preset veryfast -threads 2 \
  -c:a aac -b:a 48k -movflags +faststart "$out.tmp.mp4" && mv "$out.tmp.mp4" "$out" || exit 0
if [ "$KEEP_H" = 0 ]; then
  IFS=, read W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$out")
  if [ "$W" -gt "$H" ]; then rm -f "$out"; echo "skip horizontal: $name"; exit 0; fi
fi
echo "lite: $name"'
echo "done: $(ls lite | wc -l) proxies"
