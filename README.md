# R&B MIDI Chords

Original note-only MIDI studies of R&B chord motion. Eight studies, two variations of the keys progression. Each study is 8 bars. Harmonic intent and the pitches actually written are in the catalog. No single progression is offered as the definition of R&B. Bass guides are cataloged separately and are not part of the core count. They are not merged into the keys files.

This repository is the pack. The GitHub repository is https://github.com/mizcausevic-dev/rnb-midi-chords and it is public. The catalog page is https://mizcausevic-dev.github.io/rnb-midi-chords/ .

## What you can open

- `index.html` is the file catalog. The keys are drawn from the MIDI bytes. A pale band above E5 is left open for a vocal.
- `media.html` is the screening room. The film sits under the pictures.
- `midi/arrangement.mid` is a Format 1 preview arrangement of study 01, variation A: keys progression and bass guide.
- Individual Format 0 parts live under `midi/`.
- `midi/validation-Cursor.json` is the report from reopening those exact bytes.
- `preview/preview.mp3` is the primary music preview. It is 25.946 seconds in the encoded file. preview, not a master.
- `film/preview.mp4` and `film/preview.vtt` are the film. On-picture and caption text is `preview, not master`.
- `art/hero.jpg` is a 1280x720 illustration. `art/square.jpg` is 1080x1080. Neither is a photograph.

Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.

## Studies

- s01 Pocket: 74 BPM, 8 bars, D natural minor, tonic reference D.
- s02 Borrowed: 82 BPM, 8 bars, C major, tonic reference C.
- s03 Pedal: 68 BPM, 8 bars, A natural minor, tonic reference A.
- s04 Two Register: 90 BPM, 8 bars, G major, tonic reference G.
- s05 Plagal: 78 BPM, 8 bars, Bb major, tonic reference Bb.
- s06 Late Sus: 86 BPM, 8 bars, F major, tonic reference F.
- s07 Space: 70 BPM, 8 bars, E natural minor, tonic reference E.
- s08 No Tonic: 96 BPM, 8 bars, the eight chords, no single tonic, tonic reference no fixed tonic.

Core files: 16. Reference files: 16.

Keys stay between MIDI 48 and 76, E5, at most four notes. That ceiling is the room for a vocal. Bass guides are monophonic, MIDI 28 to 52, and are not part of the core count. C4 is 60. PPQ is 960. Meter is 4/4. Offsets are 0. Seeds identify studies and are not random draws. Generator 1.0.0. Harmonic intent, pitches, spacing, and limitations are written on each study.

## Preview path

The preview renders the canonical notes for `s01.keys.a` and `s01.bass.a` with `simple-synth-1.0.0`. Tempo authority is the encoded microsecond value in the MIDI, 810811 us per quarter note. Sample positions use `floor(seconds * 44100 + 0.5)` from tick 0. Intervals are not summed. Sample-exact repeating loops at an arbitrary BPM are not promised.

The synth mapping is a sine plus a quiet triangle for the keys and a sine for the bass. No program changes are encoded. A conventional GM player will normally use its default piano program for pitched channels unless configured otherwise; compatible GM channel 10 percussion is treated separately. Player behavior may vary. The mapping is not encoded in the MIDI.

Encoded MP3 settings: libmp3lame, 192 kbps. Film audio is AAC at 160 kbps re-encoded from that MP3, so the decoded film audio is not byte-identical to the MP3. Film duration probe: 25.946 seconds. MP3 container probe 25.946 seconds. MP4 probe 25.946 seconds. The film ends on a video frame, so it is slightly shorter than the MP3 container. The music is the same preview, not a different excerpt. The picture is a still illustration with rasterized disclosure text. DejaVu Sans Bold from the build machine supplies the glyphs. The font file is not in this pack.

No human listening audition was performed for this build. A sample peak is recorded in the preview manifest. It is not LUFS and it is not a true peak.

## Build

From the repository root, with Python 3.11+ and ffmpeg (libmp3lame, aac, libx264):

```bash
python3 tools/build_pack.py
python3 -m http.server 41773
```

The page is static. It is served with Python's HTTP server so the MIDI and media keep working relative paths. There is no application server and no package install. Standard library only.

`build/` holds the intermediate WAV, the procedural PPM, and the film plate. Those files are gitignored. The delivered audio is the MP3.

## Checks the validator actually runs

File existence, parse, PPQ, tempo, 4/4, end-of-track boundary, note pairing, ranges, monophonic bass, keys polyphony cap of four, note-off before note-on at a shared tick, absence of program changes and other channel messages, departure flags against the declared pitch-class set, agreement with the canonical score, and agreement between `arrangement.mid` and the source files. A negative overlap fixture is written outside the pack and must be rejected.

## Drafts and publication

Social captions, the X post, and the Medium article are drafts. They are not access controls. If this repository is public, the drafts are public. Do not treat them as posted to Instagram, X, or Medium.

Prepared repository description: Original note-only MIDI studies of R&B chords, with matched validation and a simple-synth preview.

Prepared topics: midi, rnb, chords, music-production, composition.

No release tag was created. `index.html` keeps its name because players and links depend on it. This page is the file catalog the pack requires. `media.html` is the screening room. GitHub Pages is served from the `gh-pages` branch.

## Limitations

Variation compatibility is per study and is written on the page. Variation A and variation B of a study are alternatives. Pair bass A with keys A, and bass B with keys B. The arrangement is only study 01. Stacking it with the part files doubles those notes. The keys stop at E5 so a vocal can sit above them. These studies are original.
