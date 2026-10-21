"""Exact word timings of a spoken line (Deepgram), to keep lines whole and cut out unwanted words.

Usage: words.py CLIP START END [LANG]     e.g. words.py IMG_3234 23 30 ru
"""
import os
import subprocess
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import raw_path  # noqa: E402,F401  (also loads .env)


def words(clip, a, b, lang='ru'):
    key = os.environ.get('DEEPGRAM_API_KEY')
    if not key:
        raise SystemExit('DEEPGRAM_API_KEY is not set')
    wav = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a), '-t', str(b - a), '-i', raw_path(clip),
                          '-ac', '1', '-ar', '16000', '-f', 'wav', '-'], capture_output=True).stdout
    r = requests.post(f'https://api.deepgram.com/v1/listen?model=nova-3&language={lang}&punctuate=true',
                      headers={'Authorization': 'Token ' + key, 'Content-Type': 'audio/wav'}, data=wav, timeout=120)
    r.raise_for_status()
    return [(w['punctuated_word'] if 'punctuated_word' in w else w['word'], a + w['start'], a + w['end'])
            for w in r.json()['results']['channels'][0]['alternatives'][0]['words']]


if __name__ == '__main__':
    ws = words(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4] if len(sys.argv) > 4 else 'ru')
    print(' '.join(f'{w}@{s:.2f}-{e:.2f}' for w, s, e in ws) or '(no speech)')
