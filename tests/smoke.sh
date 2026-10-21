#!/usr/bin/env bash
# End-to-end smoke test without API keys: synthetic clips (one SDR, one HLG) -> proxies -> peaks
# -> render -> beat grid -> beat EDL -> music mix. Checks durations of the outputs.
set -euo pipefail
S="$(cd "$(dirname "$0")/../scripts" && pwd)"
W="$(mktemp -d)"; cd "$W"; mkdir raw
ffmpeg -v error -f lavfi -i "testsrc2=size=1080x1920:rate=30:duration=6" -f lavfi -i "sine=frequency=440:duration=6" \
  -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac raw/A.mp4
ffmpeg -v error -f lavfi -i "testsrc2=size=1080x1920:rate=30:duration=6" -f lavfi -i "sine=frequency=660:duration=6" \
  -shortest -vf "format=yuv420p10le,setparams=color_primaries=bt2020:color_trc=arib-std-b67:colorspace=bt2020nc" \
  -c:v libx264 -c:a aac raw/B.mov
ffmpeg -v error -f lavfi -i "testsrc2=size=1920x1080:rate=30:duration=3" -c:v libx264 -pix_fmt yuv420p raw/H.mp4
bash "$S/make_lite.sh"
test -f lite/A.mp4 && test -f lite/B.mp4 && test ! -f lite/H.mp4
python3 "$S/audio_peaks.py"
cat > edl.json <<'EOF'
[{"video": "A", "start": 1.0, "end": 2.5}, {"video": "B.mov", "start": 0.5, "end": 2.0}, {"video": "A.mp4", "start": 3.0, "end": 4.0}]
EOF
python3 "$S/render.py" edl.json out.mp4 | tee render.log
grep -q "B.mov.*HDR" render.log  # HLG clip must be tone-mapped
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4)
python3 -c "d=float('$D'); assert abs(d - 4.3) < 0.15, d; print('render ok', d)"
python3 "$S/strip.py" --edl edl.json qa.jpg && test -s qa.jpg
# music: 120 BPM click track
ffmpeg -v error -f lavfi -i "aevalsrc='if(lt(mod(t,0.5),0.03),sin(2*PI*1000*t),0)':s=44100:d=12" track.wav
python3 "$S/music_grid.py" track.wav --len 10
cat > plan.json <<'EOF'
{"shots": [{"video": "A", "start": 0.5, "until_beat": 4, "native": 1}, {"video": "B", "start": 1.0, "until_beat": 8}],
 "last": {"video": "A", "start": 2.0, "len": 1.5}}
EOF
python3 "$S/beat_edl.py" plan.json edl_m.json
python3 "$S/render.py" edl_m.json cut.mp4 --tail 0
python3 "$S/music_mix.py" cut.mp4 edl_m.json cut_music.mp4
test -s cut_music.mp4
echo "SMOKE OK ($W)"
