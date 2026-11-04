"""Find the most spectacular moments over the FULL length of every clip -> moments.json + contact sheets.

Usage: moments.py [--per-clip 6] [--skip-start 0]

Scores every half-second of every proxy (lite/*.mp4) by contrast, change between frames and colour,
z-scored across the whole shoot. WHERE a moment sits in the file does not matter — only how good it is
(do not default to clip starts, do not avoid them either). --skip-start N only drops the first N s of
every clip when they are known to be junk (camera still being pointed). Writes moments.json = [[score, clip, t], ...]
and moments_N.jpg sheets labelled "clip@t" — look at them and build the cut from these moments only.
Works for any footage; especially useful where "events" are visual (light shows, installations, sport).
"""
import argparse
import json
import os
import subprocess
from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw


def frames(path):
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', 'fps=2,scale=48:84', '-f', 'rawvideo',
                        '-pix_fmt', 'rgb24', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, 84, 48, 3).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-clip', type=int, default=6)
    ap.add_argument('--skip-start', type=float, default=0.0)
    a = ap.parse_args()
    feats = {}
    for f in sorted(os.listdir('lite')):
        if not f.endswith('.mp4'):
            continue
        x = frames(os.path.join('lite', f))
        if len(x) < 2:
            continue
        feats[f[:-4]] = {
            'con': x.mean(axis=3).std(axis=(1, 2)),
            'diff': np.r_[0, np.abs(np.diff(x, axis=0)).mean(axis=(1, 2, 3))],
            'sat': (x.max(axis=3) - x.min(axis=3)).mean(axis=(1, 2)),
        }
    if not feats:
        raise SystemExit('no proxies in lite/ — run make_lite.sh first')
    allv = {k: np.concatenate([v[k] for v in feats.values()]) for k in ('con', 'diff', 'sat')}

    def z(k, v):
        return (v - allv[k].mean()) / (allv[k].std() + 1e-6)

    out = []
    for clip, v in feats.items():
        s = 1.0 * z('con', v['con']) + 0.8 * z('diff', v['diff']) + 0.5 * z('sat', v['sat'])
        t = np.arange(len(s)) / 2
        s[t < a.skip_start] = -1e9
        picked = []
        for i in np.argsort(-s):
            if len(picked) >= a.per_clip or s[i] < 0.3:
                break
            if all(abs(t[i] - t[j]) > 4 for j in picked):
                picked.append(i)
        out += [[round(float(s[i]), 2), clip, float(t[i])] for i in picked]
    out.sort(reverse=True)
    json.dump(out, open('moments.json', 'w'), indent=0)

    thumbs = []
    for _, clip, t in sorted(out, key=lambda m: (m[1], m[2])):
        r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', os.path.join('lite', clip + '.mp4'),
                            '-frames:v', '1', '-vf', 'scale=70:-1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                           capture_output=True)
        if r.stdout:
            thumbs.append((clip, t, Image.open(BytesIO(r.stdout)).convert('RGB')))
    cols, per = 18, 72
    for n in range(0, len(thumbs), per):
        sub = thumbs[n:n + per]
        w, h = sub[0][2].size
        S = Image.new('RGB', (w * cols, h * ((len(sub) + cols - 1) // cols)), 'white')
        D = ImageDraw.Draw(S)
        for k, (clip, t, im) in enumerate(sub):
            x, y = (k % cols) * w, (k // cols) * h
            S.paste(im, (x, y))
            D.rectangle([x, y, x + 46, y + 11], fill='black')
            D.text((x + 1, y), f'{clip[-4:]}@{t:.0f}', fill='yellow')
        S.save(f'moments_{n // per}.jpg', quality=85)
    print(f'{len(out)} moments in {len(feats)} clips -> moments.json, moments_*.jpg')


if __name__ == '__main__':
    main()
