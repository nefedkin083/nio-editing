"""Loudness peaks per clip (0.25 s windows) -> audio_peaks.json.

Loud spikes are usually events: impacts, engine revs, shouts, splashes.
They are passed to the event finder as hints.
"""
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import numpy as np


def peaks(name, max_peaks=6, min_db=8.0):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join('lite', name), '-ac', '1', '-ar', '8000',
                        '-f', 's16le', '-'], capture_output=True)
    a = np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768
    if len(a) < 4000:
        return name, []
    w = 2000
    rms = np.sqrt(np.convolve(a ** 2, np.ones(w) / w, 'valid')[::w] + 1e-9)
    db = 20 * np.log10(rms)
    med = np.median(db)
    out = []
    for i in np.argsort(-db):
        if db[i] - med < min_db or len(out) >= max_peaks:
            break
        t = i * 0.25
        if all(abs(t - p['t']) > 1.5 for p in out):
            out.append({'t': round(float(t), 2), 'db_over_median': round(float(db[i] - med), 1)})
    return name, sorted(out, key=lambda p: p['t'])


def main():
    names = sorted(n for n in os.listdir('lite') if n.endswith('.mp4'))
    with ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(peaks, names))
    json.dump(res, open('audio_peaks.json', 'w'), indent=1)
    print(sum(len(v) for v in res.values()), 'peaks in', len(res), 'clips')


if __name__ == '__main__':
    main()
