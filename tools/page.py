"""Catalog page. Keys are measured from the MIDI files.

The vocal band is empty on purpose. Bass is a separate row.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.screening import render_media, rnb_frames
from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

SPELL = {
    "s01": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s02": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"],
    "s03": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    "s04": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"],
    "s05": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
    "s06": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
    "s07": ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"],
    "s08": ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
}

SCRIPT = r"""  <script>
    const pack = JSON.parse(document.getElementById("pack").textContent);
    const rail = document.getElementById("rail");
    const scroller = document.getElementById("scroller");
    const ruler = document.getElementById("ruler");
    const keys = document.getElementById("keys");
    const bassRow = document.getElementById("bass-row");
    const status = document.getElementById("status");
    const LO = 48;
    const HI = 76;
    let studyId = "s01";
    let variation = "a";
    let keysNotes = [];
    let bassNotes = [];
    let showBass = true;
    let audio = null;
    let playing = false;
    let followId = 0;
    let rollWidth = 1200;

    function study() {
      return pack.studies.find((item) => item.id === studyId);
    }
    function pitchName(pitch) {
      return study().spell[pitch % 12] + (Math.floor(pitch / 12) - 1);
    }
    function readVlq(view, offset) {
      let value = 0;
      let byte = 0;
      do {
        byte = view.getUint8(offset);
        offset += 1;
        value = (value << 7) | (byte & 0x7f);
      } while (byte & 0x80);
      return [value, offset];
    }
    function parseMidi(buffer) {
      const view = new DataView(buffer);
      if (String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3)) !== "MThd" || view.getUint16(12) !== 960) {
        throw new Error("unexpected MIDI header");
      }
      const tracks = view.getUint16(10);
      let offset = 14;
      const notes = [];
      for (let track = 0; track < tracks; track += 1) {
        if (String.fromCharCode(view.getUint8(offset), view.getUint8(offset + 1), view.getUint8(offset + 2), view.getUint8(offset + 3)) !== "MTrk") {
          throw new Error("missing track");
        }
        const length = view.getUint32(offset + 4);
        offset += 8;
        const end = offset + length;
        let tick = 0;
        let running = 0;
        const open = new Map();
        while (offset < end) {
          let delta;
          [delta, offset] = readVlq(view, offset);
          tick += delta;
          let byte = view.getUint8(offset);
          if (byte >= 0x80) {
            running = byte;
            offset += 1;
          }
          if (running === 0xff) {
            offset += 1;
            let metaLen;
            [metaLen, offset] = readVlq(view, offset);
            offset += metaLen;
            continue;
          }
          const kind = running & 0xf0;
          const data1 = byte < 0x80 ? byte : view.getUint8(offset);
          if (byte >= 0x80) offset += 1;
          let data2 = 0;
          if (kind !== 0xc0 && kind !== 0xd0) {
            data2 = view.getUint8(offset);
            offset += 1;
          }
          const key = (running & 0x0f) + ":" + data1;
          if (kind === 0x90 && data2 > 0) open.set(key, { tick: tick, velocity: data2 });
          else if (kind === 0x80 || (kind === 0x90 && data2 === 0)) {
            const started = open.get(key);
            if (started) {
              notes.push({ pitch: data1, start: started.tick, duration: tick - started.tick, velocity: started.velocity });
              open.delete(key);
            }
          }
        }
      }
      notes.sort((a, b) => a.start - b.start || a.pitch - b.pitch);
      return notes;
    }
    function partPath(role) {
      const found = pack.parts.find((part) => part.study_id === studyId && part.role === role && part.variation === variation);
      if (!found) throw new Error("missing " + role);
      return found.path;
    }
    function renderCopy() {
      const item = study();
      document.getElementById("title").textContent = item.title;
      document.getElementById("identity").textContent = item.identity;
      document.getElementById("facts").textContent = item.id + " · " + item.bpm + " BPM · " + item.bars + " bars · " + item.collection + " · " + item.tonic;
      document.getElementById("intent").textContent = item.harmonic_intent;
      document.getElementById("pitches").textContent = item.pitches;
      document.getElementById("spacing").textContent = item.spacing;
      document.getElementById("limits").textContent = item.limitations;
      document.getElementById("departures").textContent = item.departures.length ? item.departures.join(" ") : "No pitch in this study is flagged as a departure.";
      document.getElementById("transport-label").textContent = item.title + " " + variation.toUpperCase() + " · Space plays and stops · J and K change study";
      for (const button of rail.querySelectorAll("button")) button.setAttribute("aria-pressed", button.dataset.id === studyId ? "true" : "false");
      document.getElementById("var-a").setAttribute("aria-pressed", variation === "a" ? "true" : "false");
      document.getElementById("var-b").setAttribute("aria-pressed", variation === "b" ? "true" : "false");
    }
    function draw() {
      const item = study();
      const container = item.bars * 4 * 960;
      rollWidth = Math.max(980, item.bars * 168);
      [ruler, document.getElementById("vocal-band"), keys, bassRow].forEach((node) => {
        node.style.width = rollWidth + "px";
      });
      ruler.innerHTML = "";
      let bar = 0;
      item.changes.forEach((name, index) => {
        const span = item.change_bars[index];
        const mark = document.createElement("div");
        mark.className = "change";
        mark.textContent = name;
        mark.style.left = (bar / item.bars) * rollWidth + "px";
        mark.style.width = (span / item.bars) * rollWidth + "px";
        ruler.appendChild(mark);
        bar += span;
      });
      keys.querySelectorAll(".tone").forEach((node) => node.remove());
      const fieldHeight = 220;
      keysNotes.forEach((note) => {
        const tone = document.createElement("div");
        tone.className = "tone" + (note.pitch >= 72 ? " high" : "");
        tone.title = pitchName(note.pitch) + " · MIDI " + note.pitch;
        const y = 12 + ((HI - Math.min(HI, note.pitch)) / (HI - LO)) * (fieldHeight - 28);
        tone.style.left = (note.start / container) * rollWidth + "px";
        tone.style.width = Math.max(4, (note.duration / container) * rollWidth - 2) + "px";
        tone.style.top = y + "px";
        keys.appendChild(tone);
      });
      bassRow.classList.toggle("on", showBass);
      bassRow.querySelectorAll(".bnote").forEach((node) => node.remove());
      if (showBass) {
        bassNotes.forEach((note) => {
          const mark = document.createElement("div");
          mark.className = "bnote";
          mark.title = pitchName(note.pitch) + " · MIDI " + note.pitch;
          mark.style.left = (note.start / container) * rollWidth + "px";
          mark.style.width = Math.max(8, (note.duration / container) * rollWidth - 2) + "px";
          bassRow.appendChild(mark);
        });
      }
      const highest = keysNotes.reduce((max, note) => Math.max(max, note.pitch), 0);
      const above = keysNotes.filter((note) => note.pitch > HI).length;
      if (!keysNotes.length) {
        status.textContent = "No keys notes in this variation.";
      } else if (above) {
        status.textContent = keysNotes.length + " keys notes. " + above + " sit above MIDI 76.";
      } else {
        status.textContent = keysNotes.length + " keys notes from the MIDI. Highest is " + pitchName(highest) + " (MIDI " + highest + "). The vocal band is empty.";
      }
    }
    async function loadStudy() {
      stopPlayback();
      renderCopy();
      status.textContent = "Reading the MIDI.";
      try {
        const keysRes = await fetch(partPath("keys-progression"));
        const bassRes = await fetch(partPath("bass-guide"));
        if (!keysRes.ok || !bassRes.ok) throw new Error("MIDI request failed");
        keysNotes = parseMidi(await keysRes.arrayBuffer());
        bassNotes = parseMidi(await bassRes.arrayBuffer());
        draw();
      } catch (error) {
        keysNotes = [];
        bassNotes = [];
        status.textContent = "The MIDI did not load. " + error.message;
      }
    }
    function freq(pitch) {
      return 440 * Math.pow(2, (pitch - 69) / 12);
    }
    function schedule(ctx, note, origin, amount, type) {
      const item = study();
      const seconds = (tick) => tick / 960 * item.tempo_us / 1000000;
      const when = origin + seconds(note.start);
      const duration = Math.max(0.05, seconds(note.duration));
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = type;
      osc.frequency.value = freq(note.pitch);
      const level = amount * (note.velocity / 110);
      const attack = Math.min(0.02, duration * 0.2);
      gain.gain.setValueAtTime(0.0001, when);
      gain.gain.exponentialRampToValueAtTime(Math.max(0.0002, level), when + attack);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(when);
      osc.stop(when + duration + 0.02);
    }
    function stopPlayback() {
      playing = false;
      cancelAnimationFrame(followId);
      if (audio) audio.close();
      audio = null;
      document.getElementById("play").textContent = "Play keys";
    }
    function playKeys() {
      if (!keysNotes.length) return;
      stopPlayback();
      const ctx = new AudioContext();
      if (ctx.state === "suspended") ctx.resume();
      audio = ctx;
      playing = true;
      document.getElementById("play").textContent = "Stop";
      const origin = ctx.currentTime + 0.05;
      keysNotes.forEach((note) => {
        schedule(ctx, note, origin, 0.045, "sine");
        schedule(ctx, note, origin, 0.012, "triangle");
      });
      if (showBass) bassNotes.forEach((note) => schedule(ctx, note, origin, 0.08, "sine"));
      const item = study();
      const container = item.bars * 4 * 60 / item.bpm;
      const follow = () => {
        if (!playing || !audio) return;
        if (audio.currentTime - origin < container) followId = requestAnimationFrame(follow);
        else stopPlayback();
      };
      follow();
    }
    function stepStudy(direction) {
      const index = pack.studies.findIndex((item) => item.id === studyId);
      studyId = pack.studies[(index + direction + pack.studies.length) % pack.studies.length].id;
      loadStudy();
    }
    pack.studies.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.id = item.id;
      button.textContent = item.id.slice(1) + " " + item.title;
      button.addEventListener("click", () => { studyId = item.id; loadStudy(); });
      rail.appendChild(button);
    });
    document.getElementById("var-a").addEventListener("click", () => { variation = "a"; loadStudy(); });
    document.getElementById("var-b").addEventListener("click", () => { variation = "b"; loadStudy(); });
    document.getElementById("play").addEventListener("click", () => { if (playing) stopPlayback(); else playKeys(); });
    document.getElementById("bass-toggle").addEventListener("click", () => {
      showBass = !showBass;
      document.getElementById("bass-toggle").setAttribute("aria-pressed", showBass ? "true" : "false");
      if (keysNotes.length) draw();
    });
    window.addEventListener("keydown", (event) => {
      const tag = document.activeElement && document.activeElement.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (event.code === "Space") {
        if (tag === "BUTTON" || tag === "A" || tag === "AUDIO" || tag === "VIDEO") return;
        event.preventDefault();
        if (playing) stopPlayback();
        else playKeys();
      } else if (event.key === "j" || event.key === "J") stepStudy(-1);
      else if (event.key === "k" || event.key === "K") stepStudy(1);
    });
    loadStudy();
  </script>
"""


def write_page(path: Path, catalog: dict, report: dict, preview: dict, film: dict) -> None:
    path.write_text(render_page(catalog, report, preview, film), encoding="utf-8")
    root = path.parent
    path.with_name("media.html").write_text(render_media({
        "pack_name": catalog["pack_name"],
        "subject": "The pictures show open chord spacing: a few voices with air between them, and a pale band left for a vocal.",
        "colors": {
            "bg": "#14110f",
            "paper": "#f7f1e8",
            "ink": "#1c1612",
            "accent": "#c4843a",
            "muted": "#cbb9a4",
        },
        "frames": rnb_frames(root),
        "preview_seconds": preview["seconds_encoded"],
        "film_seconds": film["duration_seconds"],
    }), encoding="utf-8")


def render_page(catalog: dict, report: dict, preview: dict, film: dict) -> str:
    rows = []
    for part in catalog["parts"]:
        kind = "core" if part["core"] else "bass guide"
        rows.append(
            "<tr>"
            f"<td><a href=\"{part['path']}\">{part['id']}</a></td>"
            f"<td>{part['role']}</td>"
            f"<td>{part['variation']}</td>"
            f"<td>{kind}</td>"
            f"<td>{part['bpm']}</td>"
            f"<td>{part['notes']}</td>"
            "</tr>"
        )
    payload = {
        "studies": [
            {
                "id": study["id"],
                "title": study["title"],
                "bpm": study["bpm"],
                "bars": study["bars"],
                "collection": study["collection_name"],
                "tonic": study["tonal_reference"],
                "identity": study["identity"],
                "limitations": study["limitations"],
                "spacing": study["spacing"],
                "departures": study["departures"],
                "harmonic_intent": study["harmonic_intent"],
                "pitches": study["pitches"],
                "changes": study["changes"],
                "change_bars": study["change_bars"],
                "tempo_us": study["tempo_us"],
                "spell": SPELL[study["id"]],
            }
            for study in catalog["studies"]
        ],
        "parts": [
            {
                "id": part["id"],
                "study_id": part["study_id"],
                "role": part["role"],
                "variation": part["variation"],
                "path": part["path"],
            }
            for part in catalog["parts"]
        ],
    }
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    seconds = f"{preview['seconds_encoded']:.2f}"
    film_seconds = f"{film['duration_seconds']:.2f}"
    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>R&amp;B MIDI Chords</title>
  <style>
    :root {{
      --bg: #14110f;
      --paper: #f7f1e8;
      --ink: #1c1612;
      --accent: #c4843a;
      --muted: #cbb9a4;
      --line: rgba(247, 241, 232, .16);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; background: var(--bg); color: var(--paper);
      font-family: Georgia, "Iowan Old Style", Palatino, serif;
      line-height: 1.45; padding-bottom: 88px;
    }}
    a {{ color: #e0b57a; }}
    button, .meta, .note, .transport, .lane-label {{ font-family: ui-monospace, Menlo, Consolas, monospace; }}
    .top {{
      position: sticky; top: 0; z-index: 6;
      display: flex; justify-content: space-between; gap: 12px; align-items: center;
      padding: 12px 20px; background: rgba(20, 17, 15, .94); border-bottom: 1px solid var(--line);
    }}
    .brand {{ letter-spacing: .14em; text-transform: uppercase; font-size: .72rem; color: var(--paper); text-decoration: none; }}
    .top nav {{ display: flex; gap: 14px; font-size: .78rem; }}
    main {{ width: min(1180px, calc(100% - 2rem)); margin: 0 auto; }}
    .stage {{
      display: grid; grid-template-columns: minmax(0, .82fr) minmax(0, 1.18fr);
      gap: 28px; align-items: start; padding: 26px 0 8px;
    }}
    .stage > div {{ min-width: 0; }}
    h1 {{ font-weight: 500; font-size: clamp(2.4rem, 5vw, 4.4rem); line-height: .92; margin: 8px 0 10px; }}
    .kicker {{ letter-spacing: .16em; text-transform: uppercase; color: var(--accent); font-size: .74rem; margin: 0; }}
    .meta, .note {{ color: var(--muted); font-size: .82rem; }}
    .hero img {{ display: block; width: 100%; height: auto; border-radius: 12px; }}
    .rail, .switch {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }}
    .rail {{ overflow-x: auto; flex-wrap: nowrap; max-width: 100%; padding-bottom: 4px; }}
    button {{
      border: 1px solid var(--line); background: transparent; color: var(--paper);
      border-radius: 999px; padding: 7px 11px; cursor: pointer;
    }}
    button[aria-pressed="true"] {{ background: var(--accent); color: #14110f; border-color: var(--accent); }}
    .scroller {{ overflow-x: auto; max-width: 100%; background: var(--paper); color: var(--ink); border-radius: 16px; }}
    .ruler, .vocal-band, .keys-field, .bass-row {{ position: relative; }}
    .ruler {{ height: 28px; background: #efe6d8; }}
    .change {{
      position: absolute; top: 4px; height: 20px; border-left: 2px solid var(--accent);
      padding-left: 5px; font-size: 11px; white-space: nowrap; overflow: hidden;
    }}
    .vocal-band {{
      height: 54px; background: #fbf7f1; color: #8a6230;
      border-bottom: 3px solid var(--accent);
      display: flex; align-items: center;
    }}
    .vocal-band span {{
      position: sticky; left: 12px;
      font-size: 12px; letter-spacing: .04em;
    }}
    .keys-field {{ height: 220px; background: var(--paper); }}
    .lane-label {{
      position: sticky; left: 8px; top: 4px; z-index: 2;
      font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: #7c6a58;
    }}
    .bass-row .lane-label {{ color: #e7d3b4; }}
    .tone {{
      position: absolute; height: 7px; border-radius: 4px; background: var(--ink); min-width: 4px;
    }}
    .tone.high {{ background: var(--accent); }}
    .bass-row {{ height: 48px; background: #14110f; color: var(--paper); display: none; }}
    .bass-row.on {{ display: block; }}
    .bnote {{
      position: absolute; top: 18px; height: 12px; border-radius: 6px; background: var(--accent);
    }}
    .legend {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: .78rem; color: var(--muted); }}
    .swatch {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }}
    .table-scroll {{ overflow-x: auto; max-width: 100%; }}
    table {{ width: 100%; border-collapse: collapse; font-size: .8rem; }}
    th, td {{ text-align: left; padding: 7px 6px; border-bottom: 1px solid var(--line); }}
    .flow {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .flow span {{ border: 1px solid var(--line); border-radius: 999px; padding: 4px 8px; font-size: .78rem; }}
    audio, video {{ display: block; width: 100%; height: auto; margin: 10px 0 16px; background: #000; }}
    .transport {{
      position: fixed; left: 0; right: 0; bottom: 0; z-index: 7;
      display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
      padding: 10px 16px; background: #100e0c; border-top: 1px solid var(--line);
    }}
    @media (max-width: 860px) {{
      .stage {{ grid-template-columns: 1fr; }}
      .top nav {{ display: none; }}
    }}
  </style>
</head>
<body>
  <header class="top">
    <a class="brand" href="index.html">R&amp;B MIDI Chords</a>
    <nav>
      <a href="#chart">Chart</a>
      <a href="#files">Files</a>
      <a href="#reading">Recorded reading</a>
      <a href="media.html">Screening room</a>
      <a href="midi/arrangement.mid">Arrangement</a>
    </nav>
  </header>
  <main>
    <section class="stage">
      <div>
        <p class="kicker">Eight studies · open spacing · room for a vocal</p>
        <h1 id="title">Pocket</h1>
        <p id="identity"></p>
        <p class="meta" id="facts"></p>
        <p id="intent"></p>
        <p id="pitches"></p>
        <p id="spacing"></p>
        <p class="note" id="limits"></p>
        <p class="note" id="departures"></p>
        <p class="note">These eight progressions are studies. None of them is the definition of R&amp;B.</p>
      </div>
      <div id="chart">
        <figure class="hero">
          <img src="art/hero.jpg" width="1280" height="720" alt="Illustration of open chord spacing on warm paper, with a pale band across the top left for a vocal. Not a photograph of a studio or of performers.">
        </figure>
        <div class="rail" id="rail"></div>
        <div class="switch">
          <button type="button" id="var-a" aria-pressed="true">Variation A</button>
          <button type="button" id="var-b" aria-pressed="false">Variation B</button>
        </div>
        <div class="scroller" id="scroller">
          <div class="ruler" id="ruler"></div>
          <div class="vocal-band" id="vocal-band">
            <span>Open for a vocal. Nothing is written above E5 (MIDI 76).</span>
          </div>
          <div class="keys-field" id="keys"><div class="lane-label">Keys progression, from the MIDI file</div></div>
          <div class="bass-row on" id="bass-row"><div class="lane-label">Bass guide, separate file</div></div>
        </div>
        <p class="legend">
          <span><i class="swatch" style="background:#1c1612"></i>keys</span>
          <span><i class="swatch" style="background:#c4843a"></i>upper voices, MIDI 72 and up</span>
          <span><i class="swatch" style="background:#fbf7f1;border:1px solid #c4843a"></i>vocal band, empty</span>
        </p>
        <p class="note" id="status">Reading the MIDI.</p>
      </div>
    </section>
    <p>{catalog['range_statement']}</p>
    <div class="flow">
      <span>Score</span><span>MIDI</span><span>Reopened validation</span><span>MP3</span><span>Film</span><span>Stills</span><span>Drafts</span>
    </div>
    <p class="note"><a href="articles/medium-draft-Cursor.md">Article draft</a> · <a href="articles/medium-paste-Cursor.txt">plain text</a></p>
    <p>{WARNING}</p>
    <h2 id="files">Files</h2>
    <p class="meta">Validation {report['result']}. Core {catalog['core_part_count']}. Bass guides {catalog['reference_part_count']}. <a href="midi/validation-Cursor.json">validation report</a> · <a href="catalog/catalog-Cursor.json">catalog</a></p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Part</th><th>Role</th><th>Var</th><th>Count</th><th>BPM</th><th>Notes</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </div>
    <section id="reading">
      <p class="kicker">Recorded reading · study 01 variation A, all 8 bars</p>
      <p>This MP3 is {seconds} seconds. {PREVIEW_LINE}. The film is {film_seconds} seconds and shows {ON_PICTURE}.</p>
      <audio controls preload="metadata" src="preview/preview.mp3"></audio>
      <p><a href="preview/preview.mp3">preview/preview.mp3</a></p>
      <video controls preload="metadata" poster="film/poster.jpg" width="1280" height="720">
        <source src="film/preview.mp4" type="video/mp4">
        <track kind="captions" src="film/preview.vtt" srclang="en" label="English" default>
      </video>
    </section>
    <p>{PROGRAM}</p>
    <p>{AUDITION}</p>
    <p>{PUBLICATION}</p>
  </main>
  <div class="transport">
    <button type="button" id="play">Play keys</button>
    <button type="button" id="bass-toggle" aria-pressed="true">Bass guide</button>
    <span id="transport-label">Space plays and stops. J and K change study.</span>
  </div>
  <script id="pack" type="application/json">{data}</script>
"""
    return head + SCRIPT + "</body>\n</html>\n"
