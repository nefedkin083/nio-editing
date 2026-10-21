"""Contact sheet with timecodes, to find the exact frame where an action starts.

Usage: strip.py CLIP START END FPS OUT.jpg [COLS]
       strip.py --edl EDL.json OUT.jpg      (3 frames per shot of an EDL, rows labelled)
"""
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import stem  # noqa: E402


def frames(clip, a, b, fps, width):
    d = tempfile.mkdtemp()
    subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-i', os.path.join('lite', stem(clip) + '.mp4'),
                    '-t', str(b - a), '-vf', f'fps={fps},scale={width}:-1', f'{d}/%04d.jpg'])
    return [Image.open(os.path.join(d, f)) for f in sorted(os.listdir(d))]


def sheet_range(clip, a, b, fps, out, cols=10):
    ims = frames(clip, a, b, fps, 110)
    if not ims:
        raise SystemExit('no frames')
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (w * cols, h * rows), 'white')
    D = ImageDraw.Draw(S)
    for k, im in enumerate(ims):
        x, y = (k % cols) * w, (k // cols) * h
        S.paste(im, (x, y))
        D.rectangle([x, y, x + 34, y + 12], fill='black')
        D.text((x + 2, y), f'{a + k / fps:.1f}', fill='yellow')
    S.save(out, quality=80)


def sheet_edl(edl_path, out):
    edl = json.load(open(edl_path))
    rows = []
    for s in edl:
        d = s['end'] - s['start']
        rows.append((s, frames(s['video'], s['start'], s['end'], 3 / max(d, 0.3), 90)[:3]))
    w, h = 90, max(im.size[1] for _, ims in rows for im in ims)
    S = Image.new('RGB', (60 + w * 3, h * len(rows)), 'white')
    D = ImageDraw.Draw(S)
    for r, (s, ims) in enumerate(rows):
        D.text((2, r * h + 2), f"{r}\n{stem(s['video'])[-6:]}\n{s['start']:.1f}", fill='black')
        for k, im in enumerate(ims):
            S.paste(im, (60 + k * w, r * h))
    S.save(out, quality=80)


if __name__ == '__main__':
    if sys.argv[1] == '--edl':
        sheet_edl(sys.argv[2], sys.argv[3])
    else:
        sheet_range(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5],
                    int(sys.argv[6]) if len(sys.argv) > 6 else 10)
