"""Build a beat-synced EDL from a short plan: each shot ends on a chosen beat.

Usage: beat_edl.py PLAN.json OUT_EDL.json

PLAN = {"intro_end": 2.44 or null,
        "shots": [{"video": "IMG_1", "start": 6.5, "until_beat": 4, "native": 0}, ...],
        "last": {"video": "IMG_9", "start": 40.0, "len": 2.9, "native": 1}}
until_beat = index in beats.json where this shot ends (cut). Shots begin where the previous one ended.
Cut points are snapped to the 30 fps frame grid so the picture never drifts from the music.
"""
import json
import sys


def q(x):
    return round(x * 30) / 30


def main():
    plan = json.load(open(sys.argv[1]))
    beats = json.load(open('beats.json'))['beats']
    cuts = [0.0] + [q(beats[s['until_beat']]) for s in plan['shots']]
    edl = []
    for i, s in enumerate(plan['shots']):
        d = cuts[i + 1] - cuts[i]
        if d <= 0:
            raise SystemExit(f'shot {i} has non-positive length; check until_beat order')
        edl.append({'video': s['video'], 'start': s['start'], 'end': round(s['start'] + d, 4),
                    'native': s.get('native', 0), 't0': cuts[i]})
    if plan.get('last'):
        last = plan['last']
        edl.append({'video': last['video'], 'start': last['start'], 'end': round(last['start'] + q(last['len']), 4),
                    'native': last.get('native', 0), 't0': cuts[-1]})
    json.dump(edl, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    total = edl[-1]['t0'] + edl[-1]['end'] - edl[-1]['start']
    print(f'{len(edl)} shots, {total:.2f}s')


if __name__ == '__main__':
    main()
