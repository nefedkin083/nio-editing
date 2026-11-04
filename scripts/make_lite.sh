#!/usr/bin/env bash
# Small proxies of every clip in raw/ -> lite/ (for Gemini and for looking).
# Default: 480p at 15 fps.  --fast: keyframes only (~1 frame/s, timecodes kept) — 4K footage on a few
# CPU cores takes hours otherwise, --fast takes seconds per clip. Gemini samples 1 frame/s anyway.
# Horizontal clips are skipped by default (reels are vertical). --keep-horizontal keeps them.
set -u
KEEP_H=0; FAST=0
for a in "$@"; do
  case "$a" in --keep-horizontal) KEEP_H=1 ;; --fast) FAST=1 ;; esac
done
mkdir -p lite
export KEEP_H FAST
find raw/ -maxdepth 1 \( -type f -o -type l \) \( -iname '*.mov' -o -iname '*.mp4' -o -iname '*.m4v' -o -iname '*.mkv' -o -iname '*.webm' \) -print0 |
xargs -0 -P 3 -I{} bash -c '
f="{}"; name=$(basename "${f%.*}"); out="lite/${name}.mp4"
[ -f "$out" ] && exit 0
if [ "$FAST" = 1 ]; then
  ffmpeg -hide_banner -loglevel error -nostdin -y -skip_frame nokey -i "$f" -map 0:v:0 -map "0:a:0?" \
    -vf "scale=-2:480" -fps_mode vfr -c:v libx264 -crf 30 -preset veryfast -threads 1 \
    -c:a aac -b:a 48k -movflags +faststart "$out.tmp.mp4" && mv "$out.tmp.mp4" "$out" || exit 0
else
  ffmpeg -hide_banner -loglevel error -nostdin -y -i "$f" -map 0:v:0 -map "0:a:0?" \
    -vf "scale=-2:480,fps=15" -c:v libx264 -crf 32 -preset veryfast -threads 2 \
    -c:a aac -b:a 48k -movflags +faststart "$out.tmp.mp4" && mv "$out.tmp.mp4" "$out" || exit 0
fi
if [ "$KEEP_H" = 0 ]; then
  IFS=, read W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$out")
  if [ "$W" -gt "$H" ]; then rm -f "$out"; echo "skip horizontal: $name"; exit 0; fi
fi
echo "lite: $name"'
echo "done: $(ls lite | wc -l) proxies"
