"""Beat grid of a music track -> beats.json + printout of bar lines (cut points).

Usage: music_grid.py TRACK [--from SEC] [--len SEC]
  --from / --len  pick the fragment you will use (e.g. the same fragment as in the Instagram sound)

Cut on bar lines (every 4 beats) for calm parts, every 2 beats for dense parts.
Put the action at the START of its bar, the hardest hit on the strongest accent.
"""
import argparse
import json
import subprocess

import librosa
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('track')
    ap.add_argument('--from', dest='start', type=float, default=0.0)
    ap.add_argument('--len', dest='length', type=float, default=0.0)
    a = ap.parse_args()
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(a.start), '-i', a.track]
    if a.length:
        cmd += ['-t', str(a.length)]
    subprocess.run(cmd + ['-ac', '2', '-ar', '44100', 'music.wav'], check=True)
    y, sr = librosa.load('music.wav', sr=22050)
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr)
    beats = librosa.frames_to_time(frames, sr=sr)
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    strength = [float(onset[min(f, len(onset) - 1)]) for f in frames]
    tempo = float(np.atleast_1d(tempo)[0])
    json.dump({'tempo': tempo, 'beats': beats.tolist(), 'strength': strength,
               'duration': float(len(y) / sr)}, open('beats.json', 'w'), indent=1)
    print(f'tempo {tempo:.0f} BPM, {len(beats)} beats, fragment {len(y) / sr:.1f}s -> music.wav, beats.json')
    print('bar lines (every 4 beats):', ' '.join(f'{b:.2f}' for b in beats[::4]))


if __name__ == '__main__':
    main()
