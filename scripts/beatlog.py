"""Second-by-second log of the best clips (Gemini Pro) -> beatlog.json.

Usage: beatlog.py [N] [clip ...]
  N      — take the top-N clips by best story_value from events.json (default 12)
  clip   — or name clips explicitly (IMG_1234 ...)
Already logged clips are skipped.
"""
import concurrent.futures as cf
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ask_gemini_video, duration, stem  # noqa: E402

MODEL = os.environ.get('BEATLOG_MODEL', 'gemini-2.5-pro')

PROMPT = """Make a detailed second-by-second log of this clip for an editor. Length {D:.1f} s.
Timecodes are SECONDS as floats from the start (never mm.ss; after 59.9 comes 60.0, 61.0 ...).
Step 1–2 seconds. For every span: what is in frame (who does what, concretely), camera movement,
what is heard (speech verbatim, impacts, engine), frame quality (sharp / blur / shake / dark).
Mark exact moments: impact, fall, start/end of an action, climax, a funny line. Write in {lang}.
Return a JSON array [{{"t0":0.0,"t1":0.0,"picture":"...","camera":"...","sound":"...","quality":"...","key":"empty or a key-moment note"}}]"""


def one(name):
    p = os.path.join('lite', name + '.mp4')
    D = duration(p)
    for _ in range(3):
        try:
            log = ask_gemini_video(p, PROMPT.format(D=D, lang=os.environ.get('EDIT_LANG', 'Russian')), MODEL)
            log = [b for b in log if isinstance(b, dict) and 't0' in b and b['t0'] <= D + 1]
            print(f'{name}: {len(log)} beats', flush=True)
            return name, log
        except Exception as ex:
            print(f'{name}: retry: {str(ex)[:120]}', flush=True)
    return name, []


def main():
    args = sys.argv[1:]
    if args and not args[0].isdigit():
        keys = [stem(a) for a in args]
    else:
        n = int(args[0]) if args else 12
        ev = json.load(open('events.json'))
        scored = [(max(e['story_value'] for e in v['events']), stem(k)) for k, v in ev.items() if v['events']]
        keys = [k for _, k in sorted(scored, reverse=True)[:n]]
    old = json.load(open('beatlog.json')) if os.path.exists('beatlog.json') else {}
    keys = [k for k in keys if k not in old]
    print(f'logging {len(keys)} clips with {MODEL}')
    with cf.ThreadPoolExecutor(6) as ex:
        old.update(dict(ex.map(one, keys)))
    json.dump(old, open('beatlog.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
