"""Find EVENTS in every proxy clip (lite/*.mp4) -> events.json.

Default model is Gemini Flash (cheap, ~$1 for 30–40 min of footage).
EVENTS_MODEL=gemini-2.5-pro for a more precise but ~5x pricier pass.
"""
import concurrent.futures as cf
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ask_gemini_video, duration  # noqa: E402

MODEL = os.environ.get('EVENTS_MODEL', 'gemini-2.5-flash')

PROMPT = """You are an editor of raw, documentary, adventure-style reels. This is one raw clip from a trip or an event.
Clip length: {D:.1f} seconds. ALL timecodes are SECONDS from the start as floats (e.g. 37.5). Never use mm.ss.

Key question: what from this clip would people retell to friends afterwards?
Look for EVENTS:
- fall: someone/something falls, a bike tips over, a crash
- stuck: stuck in mud/sand/rocks/water, wheels spinning, pulling or pushing out
- struggle: hard climb, fighting the terrain, visible effort
- stunt: jump, drift, splash, passing right next to the camera
- unusual: strange, unexpected, absurd (breaking into a car, odd place, a find)
- animal: animals
- reaction: laughter, shouting, swearing, emotion, joy after overcoming something
- reveal: a view or a place suddenly opens up
- beauty: ONLY truly strong composition (vanishing point, silhouette, backlight, fog, scale). Ordinary landscapes are not needed.

Loud audio peaks in the clip (seconds, dB over median) — often these are events: {peaks}

For every event give the setup, the peak moment and the payoff when present — this is needed for mini-stories.
Flag defects: motion blur, a finger in frame, camera pointing at the ground for no reason.
Write descriptions in {lang}.

Return STRICTLY a JSON array (may be empty if nothing strong), at most 6 items:
[{{"type": "fall|stuck|struggle|stunt|unusual|animal|reaction|reveal|beauty",
  "start": 0.0, "end": 0.0, "setup": [0.0, 0.0] or null, "peak": 0.0, "payoff": [0.0, 0.0] or null,
  "story_value": 0-10, "composition": 0-10, "sound": "what is heard",
  "description": "what happens, concretely", "defects": "defects or empty"}}]
"""


def fix_mmss(ev, D):
    """Gemini sometimes answers 1.05 meaning 1:05. If every value is tiny vs clip length, convert."""
    vals = [v for e in ev for v in (e.get('start', 0), e.get('end', 0))]
    if D > 12 and vals and max(vals) <= D / 60 + 1.01 and all((v % 1) < 0.6 for v in vals):
        for e in ev:
            for k in ('start', 'end', 'peak'):
                if isinstance(e.get(k), (int, float)):
                    m = int(e[k])
                    e[k] = m * 60 + round((e[k] - m) * 100, 2)
    return ev


def one(name):
    p = os.path.join('lite', name)
    D = duration(p)
    peaks = json.load(open('audio_peaks.json')).get(name, []) if os.path.exists('audio_peaks.json') else []
    prompt = PROMPT.format(D=D, peaks=json.dumps(peaks), lang=os.environ.get('EDIT_LANG', 'Russian'))
    for attempt in range(3):
        try:
            ev = ask_gemini_video(p, prompt, MODEL)
            ev = [e for e in ev if isinstance(e, dict) and 'start' in e and 'end' in e and 'story_value' in e]
            ev = fix_mmss(ev, D)
            ev = [e for e in ev if 0 <= e['start'] < e['end'] <= D + 0.5]
            for e in ev:
                e['end'] = min(e['end'], D - 0.05)
            print(f'{name}: {len(ev)} events', flush=True)
            return name, {'duration': D, 'events': ev}
        except Exception as ex:  # network / bad JSON
            print(f'{name}: retry {attempt}: {str(ex)[:120]}', flush=True)
    return name, {'duration': D, 'events': []}


def main():
    names = sorted(n for n in os.listdir('lite') if n.endswith('.mp4'))
    old = json.load(open('events.json')) if os.path.exists('events.json') else {}
    todo = [n for n in names if n not in old or not old[n]['events']]
    print(f'{len(todo)} clips to analyse with {MODEL}')
    with cf.ThreadPoolExecutor(6) as ex:
        old.update(dict(ex.map(one, todo)))
    json.dump(old, open('events.json', 'w'), ensure_ascii=False, indent=1)
    rows = sorted(((v, e) for v, x in old.items() for e in x['events']), key=lambda r: -r[1]['story_value'])
    print(f'TOTAL {len(rows)} events. Top:')
    for v, e in rows[:25]:
        print(f"  {v:16} {e['type']:9} {e['start']:6.1f}-{e['end']:6.1f} s{e['story_value']} c{e['composition']} "
              f"| {e['description'][:80]}")


if __name__ == '__main__':
    main()
