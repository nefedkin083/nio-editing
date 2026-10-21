"""Lay music under a rendered cut, keeping chosen moments as live sound.

Usage: music_mix.py VIDEO.mp4 EDL.json OUT.mp4 [--music music.wav] [--bed 0.25] [--duck 0.4]

EDL shots with "native": 1 play their own sound at full volume while the music ducks to --duck;
all other shots keep their own sound at --bed under full music. The EDL must carry "t0" (start of each
shot on the timeline) — write it when you build the EDL from the beat grid.
"""
import argparse
import json
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import duration  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('edl')
    ap.add_argument('out')
    ap.add_argument('--music', default='music.wav')
    ap.add_argument('--bed', type=float, default=0.25)
    ap.add_argument('--duck', type=float, default=0.4)
    a = ap.parse_args()
    e = json.load(open(a.edl))
    T = duration(a.video)
    win = []
    for i, s in enumerate(e):
        if s.get('native'):
            t0 = s['t0']
            t1 = e[i + 1]['t0'] if i + 1 < len(e) else T
            if win and abs(win[-1][1] - t0) < 0.01:
                win[-1] = (win[-1][0], t1)
            else:
                win.append((t0, t1))
    cond = '+'.join(f'between(t,{x:.3f},{y:.3f})' for x, y in win) or '0'
    fc = (f"[0:a]volume='if({cond},1.0,{a.bed})':eval=frame[n];"
          f"[1:a]atrim=0:{T},asetpts=PTS-STARTPTS,aresample=48000,"
          f"volume='if({cond},{a.duck},1.0)':eval=frame,afade=t=out:st={max(0, T - 0.6)}:d=0.6[m];"
          f"[n][m]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.video, '-i', a.music, '-filter_complex', fc,
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                    '-movflags', '+faststart', a.out], check=True)
    print('DONE', a.out, 'live-sound windows:', [(round(x, 2), round(y, 2)) for x, y in win])


if __name__ == '__main__':
    main()
