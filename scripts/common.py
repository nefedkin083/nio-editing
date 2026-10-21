"""Shared helpers: Gemini client, ffprobe, raw-file lookup.

Keys come from the environment (or a `.env` file in the project dir):
  GEMINI_API_KEY                   — Google AI Studio key (simplest), or
  GOOGLE_APPLICATION_CREDENTIALS   — Vertex AI service-account JSON (+ optional GOOGLE_CLOUD_LOCATION)
  DEEPGRAM_API_KEY                 — only for words.py (exact spoken-line timing)
"""
import glob
import json
import os
import subprocess

VIDEO_EXT = ('.mov', '.mp4', '.m4v', '.mkv', '.webm', '.avi')


def load_dotenv(path='.env'):
    if not os.path.exists(path):
        return
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()


def gemini_client():
    from google import genai
    if os.environ.get('GEMINI_API_KEY'):
        return genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    sa = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if sa and os.path.exists(sa):
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            sa, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        return genai.Client(vertexai=True, project=json.load(open(sa))['project_id'],
                            location=os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1'),
                            credentials=creds)
    raise SystemExit('No Gemini credentials: set GEMINI_API_KEY or GOOGLE_APPLICATION_CREDENTIALS')


def ask_gemini_video(path, prompt, model):
    """Send a small proxy video + prompt, return parsed JSON (list/dict)."""
    from google.genai import types
    cl = gemini_client()  # keep a reference: the client closes its session when garbage-collected
    r = cl.models.generate_content(
        model=model,
        contents=types.Content(role='user', parts=[
            types.Part(inline_data=types.Blob(data=open(path, 'rb').read(), mime_type='video/mp4')),
            types.Part(text=prompt)]),
        config=types.GenerateContentConfig(response_mime_type='application/json'))
    text = r.text.strip()
    if text.startswith('```'):
        text = text.strip('`').removeprefix('json').strip()
    return json.loads(text)


def duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def video_info(path):
    """Display width/height (rotation-aware) and color transfer."""
    r = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams',
                        '-select_streams', 'v:0', path], capture_output=True, text=True)
    s = json.loads(r.stdout)['streams'][0]
    w, h = int(s['width']), int(s['height'])
    rot = 0
    for sd in s.get('side_data_list', []) or []:
        if 'rotation' in sd:
            rot = int(sd['rotation'])
    if rot in (90, -90, 270, -270):
        w, h = h, w
    return {'width': w, 'height': h, 'transfer': s.get('color_transfer', '')}


def raw_path(name, raw_dir='raw'):
    """Find the original file for a clip name ('IMG_1.mp4', 'IMG_1' or 'IMG_1.MOV')."""
    stem = os.path.splitext(os.path.basename(name))[0]
    hits = [p for p in glob.glob(os.path.join(raw_dir, stem + '.*')) if p.lower().endswith(VIDEO_EXT)]
    if not hits:
        raise FileNotFoundError(f'no source for {name} in {raw_dir}/')
    return hits[0]


def stem(name):
    return os.path.splitext(os.path.basename(name))[0]
