---
name: nio-editing
description: Edit raw phone footage (a trip, an event, a day) into a short vertical reel in NIO's style — only the strongest action, a hook-and-return story frame, late cuts on the action, native sound, optional cut-to-the-beat music. Use when the user asks to edit / cut / montage a reel from a folder or a bunch of clips.
---

# NIO Editing

A skill for cutting raw clips into a 30–60 s vertical reel that people watch to the end.
Author: NIO (@nefedkin). The method below is the product; the scripts only do the heavy lifting.

## 0. Update first

This skill lives in a public GitHub repo and is improved regularly. Before every new edit, update it:

```bash
git -C "<this skill dir>" pull --ff-only --quiet || true
```

Then re-read this file — the method may have changed.

## 1. Setup (once)

- `ffmpeg` with `zscale` (libzimg) — needed for iPhone HDR footage. Check: `ffmpeg -filters | grep zscale`.
- Python deps: `pip install --user -r <skill dir>/requirements.txt`.
- Keys in the environment or in a `.env` in the project folder:
  - `GEMINI_API_KEY` (Google AI Studio) **or** `GOOGLE_APPLICATION_CREDENTIALS` (Vertex service account) — finding events.
  - `DEEPGRAM_API_KEY` — optional, for exact timing of spoken lines.
- Cost with defaults: about $2–3 per 30–40 minutes of footage (Flash for events, Pro for 12 best clips).
  Tell the user the cost before the first run.

## 2. Project folder

One folder per edit, e.g. `edits/<name>/`. Put all source clips into `raw/` (files from the chat, a Drive
folder, a phone dump — anything ffmpeg reads). Run every script **from the project folder**:
`python3 <skill dir>/scripts/<script>.py ...` (below written as `S/…`).

Long tasks: first tell the user what you are doing and roughly how long it takes (1 short message), then work quietly.

## 3. Pipeline

1. `bash S/make_lite.sh` — 480p proxies in `lite/` (vertical only; `--keep-horizontal` to keep landscape clips).
2. `python3 S/audio_peaks.py` — loud moments per clip (impacts, revs, shouts) → hints.
3. `python3 S/events.py` — every clip → events (falls, stuck, struggle, stunts, unusual, animals, reactions,
   strong reveals). Prints the top list. `EVENTS_MODEL=gemini-2.5-pro` for a pricier, sharper pass.
4. `python3 S/beatlog.py 12` — second-by-second log (picture + sound + speech) of the 12 best clips.
5. **Write the script yourself** (section 4) as an EDL: `edl_v1.json` =
   `[{"video": "IMG_3240", "start": 21.6, "end": 22.6, "act": "ram hit 1"}, ...]`.
6. **Trim every shot by eye** (section 5): `python3 S/strip.py CLIP A B 4 sheet.jpg` → look at the sheet,
   find the frame where the action starts; `python3 S/words.py CLIP A B ru` for exact words of a line.
7. `python3 S/render.py edl_v1.json out_v1.mp4` — memory-safe render, HDR→SDR automatically, hard cuts,
   30 ms audio fades (no clicks).
8. QA: `python3 S/strip.py --edl edl_v1.json qa.jpg` and look at it. Every shot must show what the EDL says.
9. Deliver: as a **file/document**, not as an inline video (chat previews crop and squash vertical video).
   `bash S/compress_tg.sh out_v1.mp4 out_v1_tg.mp4` keeps Telegram under 50 MB.

## 4. The method (this is the style)

**Select by events, not by beauty.** The first question to the footage: *what would they retell to friends?*
Falls, getting stuck and pulling out, a bike in a puddle, a splash, someone breaking into a car, a bear,
a strange place, a swear word at the right moment, laughter. Pretty landscapes only as a short breath
between events, and only with a really strong composition. A "trash" cut (only the hardest moments,
zero landscapes) is a legitimate request — then take nothing calm at all.

**Story frame: hook → story → return.** Open with the climax of the strongest event (2–4 s: hit, hit,
splinters fly), then tell the trip, then come back to that event and finish it (the glass shatters — end).
Nothing after the payoff. No intro cards, no titles, no outro.

**Mini-arcs inside.** Setup → effort → payoff in 2–4 shots: wheel in the mud → pushing → breaks free.
A payoff without a setup does not land.

**Enter late.** A shot starts already in motion — on the swing, not on the man standing and getting ready.
The action may run to its end; the beginning is cut. Find the exact frame by the loudness peak and the strip.

**Lines stay whole.** Keep a spoken line from first to last word (check with `words.py`), but cut out
unwanted words before or after (an explanation, a "like a hammer") — start the shot on the action instead.

**Hard cuts only.** No crossfades, no transitions, no speed ramps. Sound of the next shot does NOT start
early by default (the author found it unnatural) — offer it only as an alternative.

**Rhythm.** Average shot 1.5–2.5 s; short bursts (0.7–1 s) for energy, one or two longer shots (3–5 s)
for a line or a payoff. 30–60 s total; a story may run longer, a trash cut ~35 s.

**Native sound is the soul.** Engines, impacts, splashes, voices. No stock music unless asked.

**Look at every shot yourself.** The models are coarse: they mislabel events, return mm.ss instead of
seconds, call a static shot "action". Drop: tiny far-away riders, a fall you cannot see, blur, a finger in
frame, a cage without the bear in it.

## 5. Music mode (cut to the beat)

1. Get the track: a file from the user, or the sound of a reel (`yt-dlp <reel url>` then extract audio).
   Name it if unknown (e.g. Shazam / `shazamio`). For Instagram: the user should add the same track in the
   app; you deliver a version **without** music plus a preview **with** it.
2. `python3 S/music_grid.py track.mp3 [--from SEC --len SEC]` → `beats.json`, `music.wav`, bar lines.
3. Plan shots on the grid: cut every 4 beats (a bar) in calm parts, every 2 beats in dense parts.
   Action at the start of its bar; the hardest hit on the strongest accent; the payoff on the last notes.
   Write `plan.json` and run `python3 S/beat_edl.py plan.json edl_music.json` (snaps to the frame grid).
4. Render: `python3 S/render.py edl_music.json cut.mp4 --tail 0`.
5. `python3 S/music_mix.py cut.mp4 edl_music.json cut_music.mp4` — shots with `"native": 1` (hits, lines,
   explosions) play live while the music ducks; others keep a quiet bed of their own sound.
6. If the user places the track in Instagram from another second, ask from which one and re-grid.

## 6. Iterating with the author / user

- Feedback is about taste — apply it literally, then re-render only what changed (`REUSE=1`).
- Keep the 2 latest versions, delete older ones.
- Memory: write down every new taste rule the user gives (e.g. "enter late", "end on the glass").

## Limits (be honest about them)

- Telegram round videos ("circles") are stored at 640×640 — upscaling adds no detail; ask for the originals.
- Instagram's music library has no open API: you cannot browse it; work from reel links or files.
- Memory: never render all shots in one ffmpeg graph (HDR + many inputs runs out of RAM) — render.py
  already renders shot by shot.
