"""Render an EDL to a vertical reel. Hard cuts, native sound, 30 ms audio fades on every cut.

Usage: render.py EDL.json OUT.mp4 [--size 1080x1920] [--tail 0.3]

EDL = JSON list of {"video": "IMG_1234", "start": 12.3, "end": 14.0, ...} in cut order; sources in raw/.
Memory-safe: each shot is rendered on its own (HDR iPhone footage is tone-mapped to SDR per shot),
then shots are joined one after another. REUSE=1 keeps already rendered shots in segs/.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import raw_path, video_info  # noqa: E402

TONEMAP = ('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,'
           'tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p')
HDR_TRANSFERS = ('arib-std-b67', 'smpte2084')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.returncode, r.stderr[-2000:])
        sys.exit(1)


def render(edl_path, out_path, W=1080, H=1920, tail=0.3):
    edl = json.load(open(edl_path))
    os.makedirs('segs', exist_ok=True)
    segs = []
    for i, s in enumerate(edl):
        src = raw_path(s['video'])
        d = s['end'] - s['start'] + (tail if i == len(edl) - 1 else 0)
        out = os.path.join('segs', f'seg_{i:03d}.mov')
        segs.append(out)
        if os.environ.get('REUSE') and os.path.exists(out) and i < len(edl) - 1:
            continue
        hdr = video_info(src)['transfer'] in HDR_TRANSFERS
        vf = (TONEMAP + ',' if hdr else 'format=yuv420p,') + \
            f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30'
        af = (f'aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{d:.3f},'
              f'afade=t=in:st=0:d=0.03,afade=t=out:st={max(0, d - 0.03):.3f}:d=0.03')
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-threads', '2',
             '-ss', f"{s['start']:.3f}", '-i', src, '-t', f'{d:.3f}',
             '-filter_complex', f'[0:v:0]{vf}[v];[0:a:0]{af}[a]' if has_audio(src)
             else f'[0:v:0]{vf}[v];anullsrc=r=48000:cl=stereo,atrim=0:{d:.3f}[a]',
             '-map', '[v]', '-map', '[a]', '-t', f'{d:.3f}',
             '-c:v', 'libx264', '-crf', '16', '-preset', 'fast', '-pix_fmt', 'yuv420p', '-c:a', 'pcm_s16le', out])
        print(f"shot {i:2d} {s['video']} {s['start']:.2f}+{d:.2f}s{' HDR' if hdr else ''}", flush=True)
    lst = os.path.join('segs', 'list.txt')
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in segs))
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
         '-r', '30', '-c:v', 'libx264', '-crf', '21', '-preset', 'medium', '-pix_fmt', 'yuv420p',
         '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
         '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out_path])
    print('DONE', out_path, round(os.path.getsize(out_path) / 1e6, 1), 'MB')


def has_audio(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index',
                        '-of', 'csv=p=0', path], capture_output=True, text=True)
    return bool(r.stdout.strip())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('edl')
    ap.add_argument('out')
    ap.add_argument('--size', default='1080x1920')
    ap.add_argument('--tail', type=float, default=0.3, help='extra seconds on the last shot')
    a = ap.parse_args()
    w, h = map(int, a.size.split('x'))
    render(a.edl, a.out, w, h, a.tail)
