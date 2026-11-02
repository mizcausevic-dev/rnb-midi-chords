"""Original R&B chord studies.

Tempos, lengths, and collections are fixed before the notes. Keys stay at
or below E5 so a vocal can sit above them. Bass guides are separate files
and are not core. Offsets are 0. No single progression is offered as the genre.
"""

from __future__ import annotations

from tools.midi_io import BAR_TICKS_4_4, PPQ, bpm_to_us, effective_bpm

GENERATOR_VERSION = "1.0.0"
PACK_ID = "rnb-midi-chords"
PACK_NAME = "R&B MIDI Chords"
BAR = BAR_TICKS_4_4
VOCAL_CEILING = 76


class Part:
    def __init__(self, study, part_id, role, variation, core, channel, slug, mono, poly, lo, hi):
        self.study = study
        self.part_id = part_id
        self.role = role
        self.variation = variation
        self.core = core
        self.channel = channel
        self.file_slug = slug
        self.monophonic = mono
        self.max_poly = poly
        self.lo = lo
        self.hi = hi
        self.container_ticks = study["bars"] * BAR
        self.notes = []

    def add(self, start, duration, pitch, velocity, departure=False):
        end = start + duration
        if start < 0 or duration <= 0 or end > self.container_ticks:
            raise ValueError(f"{self.part_id} boundary {start}+{duration}")
        if not self.lo <= pitch <= self.hi:
            raise ValueError(f"{self.part_id} pitch {pitch}")
        active = 1
        for other in self.notes:
            o0 = other["performed_start"]
            o1 = o0 + other["duration"]
            if start < o1 and o0 < end:
                if other["pitch"] == pitch or self.monophonic:
                    raise ValueError(f"{self.part_id} overlap {pitch}@{start}")
                active += 1
        if active > self.max_poly:
            raise ValueError(f"{self.part_id} poly {active}")
        self.notes.append({
            "nominal_start": start, "offset": 0, "performed_start": start,
            "duration": duration, "pitch": pitch, "velocity": velocity,
            "channel": self.channel, "departure": departure,
        })

    def finish(self):
        ordered = sorted(self.notes, key=lambda n: (n["performed_start"], n["pitch"]))
        if self.core and len(ordered) < 8:
            raise ValueError(f"{self.part_id} too few notes")
        if not ordered:
            raise ValueError(f"{self.part_id} empty")
        for index, note in enumerate(ordered, 1):
            note["id"] = f"{self.part_id}.n{index:04d}"
        return {
            "id": self.part_id, "study_id": self.study["id"], "slug": self.study["slug"],
            "role": self.role, "variation": self.variation, "core": self.core,
            "channel": self.channel, "file_slug": self.file_slug,
            "path": f"midi/{self.study['slug']}/{self.file_slug}.mid",
            "monophonic": self.monophonic, "max_poly": self.max_poly,
            "container_ticks": self.container_ticks, "container_bars": self.study["bars"],
            "bpm": self.study["bpm"], "tempo_us": self.study["tempo_us"], "notes": ordered,
        }


def keys(study, variation):
    return Part(study, f"{study['id']}.keys.{variation}", "keys-progression", variation, True, 0, f"keys-{variation}", False, 4, 48, VOCAL_CEILING)


def bass(study, variation):
    return Part(study, f"{study['id']}.bass.{variation}", "bass-guide", variation, False, 1, f"bass-{variation}", True, 1, 28, 52)


def bar(n, beat=0):
    """Bar `n` plus `beat` quarter notes. Beat 0 is the downbeat."""
    return n * BAR + beat * PPQ


def chord(part, start, duration, voices, velocity):
    for pitch, departure in voices:
        part.add(start, duration, pitch, velocity, departure=departure)


def n(pitch, departure=False):
    return (pitch, departure)


def studies():
    rows = [
        {"id": "s01", "slug": "s01-pocket", "title": "Pocket", "bpm": 74, "bars": 8,
         "tonic": "D", "tonal_reference": "D", "collection_name": "D natural minor",
         "pitch_classes": [2, 4, 5, 7, 9, 10, 0],
         "departures": ["Bar 4 is A7. C#4 (61) is the third and is flagged. The E and G beside it stay in D natural minor."],
         "seed": 7401,
         "harmonic_intent": "Variation A is Dm9, Gm9, Bbmaj7, A7, then a lower Dm9, Gm11, Bbmaj7, and Am7. The last chord is Am7, not a return to D. Those extension names are variation A. Variation B does not sound them.",
         "changes": ["Dm9", "Gm9", "Bbmaj7", "A7", "Dm9", "Gm11", "Bbmaj7", "Am7"],
         "changes_b": ["F5", "G5", "Bb5", "E C# G", "D A E", "F5", "F D A", "A5"],
         "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "pitches": "Variation A: Dm9 is F A C E. Gm9 is Bb D F A. Bar 3 Bbmaj7 is D F A, root omitted. Bar 7 is Bb F A, third omitted. A7 is C# E G. Gm11 is Bb D F C. Am7 is C E G A. Variation B is not those voicings. Its keys are bare fifths on F, G, Bb, F, and A, plus D A E, F D A, and the A7 tritone E C# G.",
         "identity": "Each chord in variation A enters on the downbeat and leaves beat 4 empty. Variation B waits until beat 2. Its keys are mostly bare fifths: F, G, Bb, then F and A again. Bar 5 is D A E. Bar 7 is F D A, and bass B plays F under it, not Bb. Bar 4 is E C# G. C# up to G is a tritone, not a fourth, fifth, or sixth.",
         "limitations": "Bass A fits variation A. Bass B fits variation B. The empty beat is space, not a missing chord.",
         "spacing": "Variation A is close voicing, top note at or below E5. Variation B uses three open notes and does not reach E5."},
        {"id": "s02", "slug": "s02-borrowed", "title": "Borrowed", "bpm": 82, "bars": 8,
         "tonic": "C", "tonal_reference": "C", "collection_name": "C major",
         "pitch_classes": [0, 2, 4, 5, 7, 9, 11],
         "departures": ["Abmaj7 uses Ab (68) and Eb (75). Fm uses Ab (68). The bass guide plays Ab (44) under those bars. Those pitches are flagged. C and G in the same chords stay in C major."],
         "seed": 8202,
         "harmonic_intent": "Cmaj7, Abmaj7, Fm, G7, Cmaj9, Abmaj7, Dm7, G7sus. Ab and F minor are borrowed. They are not the home key.",
         "changes": ["Cmaj7", "Abmaj7", "Fm", "G7", "Cmaj9", "Abmaj7", "Dm7", "G7sus"],
         "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "pitches": "Cmaj7 is E G B. The first Abmaj7 is G Ab C Eb. The second Abmaj7 is Ab C Eb. Fm is F Ab C. G7 is F G B. Cmaj9 is D E G B. Dm7 is F A C. G7sus is F G C. Ab and Eb are flagged.",
         "identity": "Variation A starts every chord on beat 2 and holds it for two beats, so the downbeat is a rest. Variation B starts on the downbeat. On the two borrowed bars it plays the Ab chord for one beat, then E G C.",
         "limitations": "The borrowed chords are the color. Do not treat Ab major as the tonic.",
         "spacing": "Guide tones, three or four notes, top voice at or below Eb5."},
        {"id": "s03", "slug": "s03-pedal", "title": "Pedal", "bpm": 68, "bars": 8,
         "tonic": "A", "tonal_reference": "A", "collection_name": "A natural minor",
         "pitch_classes": [9, 11, 0, 2, 4, 5, 7], "departures": [], "seed": 6803,
         "harmonic_intent": "Bass A plays A, A, F, E, A, F, D, A. The keys play Am9, Cmaj7, Fmaj7, Em7, Am9, Fmaj7, Dm7, and Am. The second half is not the first half moved down a step.",
         "changes": ["Am9", "Cmaj7", "Fmaj7", "Em7", "Am9", "Fmaj7", "Dm7", "Am"],
         "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "pitches": "Am9 is C E G B. Cmaj7 is E G B. Fmaj7 is F A C E. Em7 is D E G B. Dm7 is F A C. The last Am is A E A.",
         "identity": "After bar 1, each chord arrives a sixteenth early. Variation B stays on the downbeat and thins to two notes.",
         "limitations": "The early attack ends before the next early attack. Nothing starts before tick 0.",
         "spacing": "The pedal is only in the bass file. The keys never double it on the same beat as a second bass."},
        {"id": "s04", "slug": "s04-two-register", "title": "Two Register", "bpm": 90, "bars": 8,
         "tonic": "G", "tonal_reference": "G", "collection_name": "G major",
         "pitch_classes": [7, 9, 11, 0, 2, 4, 6], "departures": [], "seed": 9004,
         "harmonic_intent": "Gmaj9, E and B, Am7, D7, then G, E and B, Cmaj7, and D major. Bars 2 and 6 are only E and B over E, not Em7. Bar 4 is D7: bass D with C and F#, and the beat-3 tone is D, not a ninth. Bar 8 is D A F#, D major, not D7. Beat 1 is the shell. Beat 3 is a higher color tone still under the vocal ceiling.",
         "changes": ["Gmaj9", "E5", "Am7", "D7", "G", "E5", "Cmaj7", "D"],
         "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "pitches": "Variation A, beat 1 then beat 3: B F# then A, B E then B, C G then C, C F# then D, B F# then G, B E then B, E B then C, D A then F#. Bars 2 and 6 are E and B, not Em7. Bar 4 is D7, not D9. Bar 8 is D major, not D7. All of those pitch classes are inside G major.",
         "identity": "Two attacks in every bar, on beat 1 and beat 3. Variation B swaps them: the color comes first and the shell answers.",
         "limitations": "The two attacks are one progression, not two songs. Use one bass file with one keys variation.",
         "spacing": "Beat 1 sits from B3 to B4. Bar 7 beat 1 is E4 and B4. Beat 3 sits between F#4 and D5 and stays under E5."},
        {"id": "s05", "slug": "s05-plagal", "title": "Plagal", "bpm": 78, "bars": 8,
         "tonic": "Bb", "tonal_reference": "Bb", "collection_name": "Bb major",
         "pitch_classes": [10, 0, 2, 3, 5, 7, 9],
         "departures": ["The minor iv is Ebm. Gb4 (66) is flagged. Eb and Bb in that chord stay in Bb major."],
         "seed": 7805,
         "harmonic_intent": "Two bars of Bbmaj7, two of Ebmaj7, two of Ebm, two of Bbmaj9. The minor iv is the color, then the major I returns with a ninth.",
         "changes": ["Bbmaj7", "Ebmaj7", "Ebm", "Bbmaj9"],
         "change_bars": [2, 2, 2, 2],
         "pitches": "Bbmaj7 is D F A. Ebmaj7 is G Bb D. Ebm is Eb Gb Bb. Bbmaj9 is C F A.",
         "identity": "Each chord in variation A is held for two bars. Variation B uses one bar of the chord, then one bar on a single tone: G, Gb, F, then D.",
         "limitations": "Gb is outside Bb major and is flagged. Variation A uses it only in the Ebm bars. Variation B also holds that Gb alone on bar 4, before Ebm. It is not a new key.",
         "spacing": "Three-note chords with a gap of a third or a fourth between voices."},
        {"id": "s06", "slug": "s06-late-sus", "title": "Late Sus", "bpm": 86, "bars": 8,
         "tonic": "F", "tonal_reference": "F", "collection_name": "F major",
         "pitch_classes": [5, 7, 9, 10, 0, 2, 4], "departures": [], "seed": 8606,
         "harmonic_intent": "Fsus2, Bbmaj9, E F Bb, Fmaj7, Gm9, Am7, Bb6, C9. The third bar's keys are E F Bb. C is only in the bass, so those keys are not a C11. Fsus2 is the suspension. It resolves at Fmaj7, not before.",
         "changes": ["Fsus2", "Bbmaj9", "E F Bb", "Fmaj7", "Gm9", "Am7", "Bb6", "C9"],
         "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "pitches": "Fsus2 is F G C. Bbmaj9 is C D F A. The third bar's keys are E F Bb, and variation A also sounds E5. C3 is only in the bass. Fmaj7 is E F A. Gm9 is Bb D F A. Am7 is C E G. Bb6 is D G Bb. C9 is D E Bb.",
         "identity": "Variation A starts every chord on the second eighth and holds it for three beats. Variation B moves the same harmony onto beat 4 as a short stab.",
         "limitations": "The late entrance is the pocket. Do not move these chords to the downbeat and call it the same study.",
         "spacing": "Four notes only where the extension needs them. Several chords are three notes."},
        {"id": "s07", "slug": "s07-space", "title": "Space", "bpm": 70, "bars": 8,
         "tonic": "E", "tonal_reference": "E", "collection_name": "E natural minor",
         "pitch_classes": [4, 6, 7, 9, 11, 0, 2],
         "departures": ["Bar 7 is B7. D#4 (63) is flagged. F# and A beside it are inside E natural minor."],
         "seed": 7007,
         "harmonic_intent": "Variation A is Em9, silence, Am9, silence, Cmaj7, silence, B7, silence. The empty bars are the vocal bars in variation A only. Variation B has a keys note on every bar.",
         "changes": ["Em9", "rest", "Am9", "rest", "Cmaj7", "rest", "B7", "rest"],
         "changes_b": ["Em9", "B", "Am9", "C", "Cmaj7", "E", "B7", "F#"],
         "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "pitches": "Em9 is G B D F#. Am9 is G B C E. Cmaj7 is G B E. B7 is D# F# A.",
         "identity": "A chord only on the odd bars, held for that one bar. Variation B fills the even bars with a single whole-note guide tone.",
         "limitations": "The rests are written. They are not a loop that failed to copy.",
         "spacing": "The chord uses the middle register. Variation A leaves the even bars empty, with no keys notes. Variation B puts one whole-note guide tone on each even bar: B, C, E, then F#."},
        {"id": "s08", "slug": "s08-no-tonic", "title": "No Tonic", "bpm": 96, "bars": 8,
         "tonic": "none", "tonal_reference": "no fixed tonic", "collection_name": "the eight chords, no single tonic",
         "pitch_classes": [0, 1, 2, 3, 4, 5, 6, 7, 9, 11],
         "departures": [],
         "seed": 9608,
         "harmonic_intent": "Em7, A7, Dm7, G7, F#m7, B7, then Em and A. The last Em is E G B, with no seventh. The last A is E A C#, with no seventh. The line never lands on one tonic. Calling any one chord the key would be a guess. C#, D#, and F# are inside the declared set because A7, B7, and F#m7 use them.",
         "changes": ["Em7", "A7", "Dm7", "G7", "F#m7", "B7", "Em", "A"],
         "change_bars": [1, 1, 1, 1, 1, 1, 1, 1],
         "pitches": "Each bar is three shell tones in quarter notes, and the fourth quarter repeats the first: G3 B3 D4 G3, G3 C#4 E4 G3, F3 A3 C4 F3, F3 B3 D4 F3, F#3 A3 C#4 F#3, F#3 A3 D#4 F#3, then E3 G3 B3 E3 and E3 A3 C#4 E3. The last two are not an octave below the first two. Bar 2's C#4 returns at the same pitch in bar 8.",
         "identity": "Variation A plays one note at a time, a quarter each. Variation B stacks the three shell tones and holds them.",
         "limitations": "There is no tonic to resolve to. The last A7 is the end of the phrase, not a mistake.",
         "spacing": "The arpeggio stays between E3 and E4. The stacked variation sounds those three pitches together."},
    ]
    for row in rows:
        if not 65 <= row["bpm"] <= 100:
            raise ValueError(row["bpm"])
        if sum(row["change_bars"]) != row["bars"]:
            raise ValueError(row["id"])
        row["tempo_us"] = bpm_to_us(row["bpm"])
        row["effective_bpm"] = effective_bpm(row["tempo_us"])
        row["meter"] = "4/4"
        row["bar_ticks"] = BAR
        row["ppq"] = PPQ
        row["stochastic_draws"] = 0
        row["vocal_ceiling"] = VOCAL_CEILING
    return rows


def _pair(study):
    return keys(study, "a"), keys(study, "b"), bass(study, "a"), bass(study, "b")


def _roots(part, pitches, pocket, departures=()):
    flagged = set(departures)
    for index, pitch in enumerate(pitches):
        for offset, duration, velocity in pocket:
            part.add(bar(index) + offset, duration, pitch, velocity, departure=pitch in flagged)


def _s01(study):
    a, b, ba, bb = _pair(study)
    blocks = [
        [n(65), n(69), n(72), n(76)],
        [n(58), n(62), n(65), n(69)],
        [n(62), n(65), n(69)],
        [n(61, True), n(64), n(67)],
        [n(53), n(57), n(60), n(64)],
        [n(58), n(62), n(65), n(72)],
        [n(58), n(65), n(69)],
        [n(60), n(64), n(67), n(69)],
    ]
    open_b = [
        [n(53), n(60), n(65)],
        [n(55), n(62), n(67)],
        [n(58), n(65), n(70)],
        [n(52), n(61, True), n(67)],
        [n(50), n(57), n(64)],
        [n(53), n(60), n(65)],
        [n(53), n(62), n(69)],
        [n(57), n(64), n(69)],
    ]
    for index, voices in enumerate(blocks):
        chord(a, bar(index), BAR - PPQ, voices, 74 + (index % 4) * 6)
    for index, voices in enumerate(open_b):
        chord(b, bar(index, 1), PPQ * 2, voices, 80)
    _roots(ba, (38, 43, 46, 45, 38, 43, 46, 45), [(0, BAR - PPQ, 96)])
    _roots(bb, (50, 43, 46, 45, 38, 43, 41, 45), [(PPQ, PPQ * 2, 90)])
    return [a, b, ba, bb]


def _s02(study):
    a, b, ba, bb = _pair(study)
    blocks = [
        [n(64), n(67), n(71)],
        [n(67), n(68, True), n(72), n(75, True)],
        [n(65), n(68, True), n(72)],
        [n(65), n(67), n(71)],
        [n(62), n(64), n(67), n(71)],
        [n(68, True), n(72), n(75, True)],
        [n(65), n(69), n(72)],
        [n(65), n(67), n(72)],
    ]
    for index, voices in enumerate(blocks):
        chord(a, bar(index, 1), PPQ * 2, voices, 78 + (index % 4) * 4)
    # B: the borrowed bar resolves to C inside the same bar.
    for index, voices in enumerate(blocks):
        if index in (1, 5):
            chord(b, bar(index), PPQ, voices, 90)
            chord(b, bar(index, 2), PPQ * 2, [n(64), n(67), n(72)], 76)
        else:
            chord(b, bar(index), BAR - PPQ // 2, voices, 76)
    _roots(ba, (36, 44, 41, 43, 36, 44, 38, 43), [(PPQ, PPQ * 2, 94)], departures=(44,))
    _roots(bb, (48, 44, 41, 43, 48, 44, 50, 43), [(0, PPQ, 100), (PPQ * 2, PPQ, 82)], departures=(44,))
    return [a, b, ba, bb]


def _s03(study):
    a, b, ba, bb = _pair(study)
    blocks = [
        [n(60), n(64), n(67), n(71)],
        [n(64), n(67), n(71)],
        [n(65), n(69), n(72), n(76)],
        [n(62), n(64), n(67), n(71)],
        [n(60), n(64), n(67), n(71)],
        [n(65), n(69), n(72), n(76)],
        [n(65), n(69), n(72)],
        [n(57), n(64), n(69)],
    ]
    for index, voices in enumerate(blocks):
        if index == 0:
            chord(a, 0, BAR - PPQ // 4, voices, 72)
        else:
            chord(a, bar(index) - PPQ // 4, BAR - PPQ // 4, voices, 76 + (index % 4) * 4)
    for index, voices in enumerate(blocks):
        chord(b, bar(index), PPQ * 3, voices[:2], 70 + index)
    _roots(ba, (33, 33, 41, 40, 33, 41, 38, 33), [(0, BAR, 88)])
    _roots(bb, (45, 45, 41, 40, 45, 41, 50, 45), [(PPQ // 2, PPQ * 2, 92)])
    return [a, b, ba, bb]


def _s04(study):
    a, b, ba, bb = _pair(study)
    shells = [
        [n(59), n(66)],
        [n(59), n(64)],
        [n(60), n(67)],
        [n(60), n(66)],
        [n(59), n(66)],
        [n(59), n(64)],
        [n(64), n(71)],
        [n(62), n(69)],
    ]
    colors = [
        [n(69)],
        [n(71)],
        [n(72)],
        [n(74)],
        [n(67)],
        [n(71)],
        [n(72)],
        [n(66)],
    ]
    for index, (shell, color) in enumerate(zip(shells, colors)):
        chord(a, bar(index), PPQ, shell, 86)
        chord(a, bar(index, 2), PPQ, color, 74)
        chord(b, bar(index), PPQ, color, 78)
        chord(b, bar(index, 2), PPQ * 2, shell, 90)
    _roots(ba, (43, 40, 45, 38, 43, 40, 48, 38), [(0, PPQ, 100), (PPQ * 2, PPQ, 84)])
    _roots(bb, (31, 40, 33, 38, 31, 40, 36, 38), [(PPQ * 2, PPQ, 96)])
    return [a, b, ba, bb]


def _s05(study):
    a, b, ba, bb = _pair(study)
    held = [
        (0, [n(62), n(65), n(69)]),
        (2, [n(67), n(70), n(74)]),
        (4, [n(63), n(66, True), n(70)]),
        (6, [n(60), n(65), n(69)]),
    ]
    for start, voices in held:
        chord(a, bar(start), 2 * BAR, voices, 80 if start < 6 else 96)
    # B: bar of the chord, then a bar on the third of the next harmony.
    thirds = [
        (0, [n(62), n(65), n(69)], [n(67)]),
        (2, [n(67), n(70), n(74)], [n(66, True)]),
        (4, [n(63), n(66, True), n(70)], [n(65)]),
        (6, [n(60), n(65), n(69)], [n(62)]),
    ]
    for start, block, third in thirds:
        chord(b, bar(start), BAR, block, 84)
        chord(b, bar(start + 1), BAR, third, 70)
    _roots(ba, (34, 34, 39, 39, 39, 39, 34, 34), [(0, 2 * PPQ, 92)])
    # bass A two-bar roots would overlap if I use per-bar with duration 2*PPQ from each bar.
    ba.notes.clear()
    for index, pitch in enumerate((34, 39, 39, 34)):
        ba.add(bar(index * 2), 2 * BAR, pitch, 92)
    for index, pitch in enumerate((46, 46, 51, 51, 51, 51, 46, 46)):
        bb.add(bar(index), BAR - PPQ, pitch, 88)
    return [a, b, ba, bb]


def _s06(study):
    a, b, ba, bb = _pair(study)
    blocks = [
        [n(65), n(67), n(72)],
        [n(60), n(62), n(65), n(69)],
        [n(64), n(65), n(70), n(76)],
        [n(64), n(65), n(69)],
        [n(58), n(62), n(65), n(69)],
        [n(60), n(64), n(67)],
        [n(62), n(67), n(70)],
        [n(62), n(64), n(70)],
    ]
    for index, voices in enumerate(blocks):
        chord(a, bar(index) + PPQ // 2, PPQ * 3, voices, 76 + (index % 4) * 6)
        chord(b, bar(index, 3), PPQ, voices[:3], 96 if index >= 6 else 72)
    _roots(ba, (41, 46, 48, 41, 43, 45, 46, 48), [(PPQ // 2, PPQ * 2, 94)])
    _roots(bb, (29, 34, 36, 29, 31, 33, 34, 36), [(PPQ * 3, PPQ, 98)])
    return [a, b, ba, bb]


def _s07(study):
    a, b, ba, bb = _pair(study)
    blocks = {
        0: [n(55), n(59), n(62), n(66)],
        2: [n(55), n(59), n(60), n(64)],
        4: [n(55), n(59), n(64)],
        6: [n(63, True), n(66), n(69)],
    }
    for index, voices in blocks.items():
        chord(a, bar(index), BAR, voices, 84 if index < 6 else 104)
    guides = {1: n(59), 3: n(60), 5: n(64), 7: n(66)}
    for index, voice in guides.items():
        chord(b, bar(index), BAR, [voice], 68)
    for index, voices in blocks.items():
        chord(b, bar(index), BAR - PPQ, voices, 86)
    _roots(ba, (40, 40, 45, 45, 48, 48, 47, 47), [(0, PPQ * 2, 90)])
    ba.notes.clear()
    for index, pitch in ((0, 40), (2, 45), (4, 48), (6, 47)):
        ba.add(bar(index), BAR, pitch, 94)
    for index, pitch in enumerate((40, 40, 45, 45, 48, 48, 47, 52)):
        bb.add(bar(index), PPQ * 2, pitch, 86)
    return [a, b, ba, bb]


def _s08(study):
    a, b, ba, bb = _pair(study)
    lines = [
        [n(55), n(59), n(62)],
        [n(55), n(61), n(64)],
        [n(53), n(57), n(60)],
        [n(53), n(59), n(62)],
        [n(54), n(57), n(61)],
        [n(54), n(57), n(63)],
        [n(52), n(55), n(59)],
        [n(52), n(57), n(61)],
    ]
    for index, voices in enumerate(lines):
        for beat, voice in enumerate(voices):
            chord(a, bar(index, beat), PPQ, [voice], 80 if beat == 0 else 68)
        chord(a, bar(index, 3), PPQ, [voices[0]], 64)
        chord(b, bar(index), BAR - PPQ // 2, voices, 82)
    _roots(ba, (40, 45, 38, 43, 42, 47, 40, 45), [(0, PPQ, 100), (PPQ * 2, PPQ, 78)])
    _roots(bb, (40, 45, 38, 43, 42, 47, 40, 33), [(0, BAR - PPQ, 92)])
    return [a, b, ba, bb]


BUILDERS = {f"s0{i}": fn for i, fn in enumerate([_s01, _s02, _s03, _s04, _s05, _s06, _s07, _s08], 1)}


def _sig(notes):
    return tuple((note["performed_start"], note["pitch"], note["duration"]) for note in notes)


def assert_collections(catalog_studies, parts):
    allowed = {study["id"]: set(study["pitch_classes"]) for study in catalog_studies}
    for part in parts:
        pool = allowed[part["study_id"]]
        for note in part["notes"]:
            inside = (note["pitch"] % 12) in pool
            if note["departure"] and inside:
                raise ValueError(f"{part['id']} departure {note['pitch']} is inside the collection")
            if not note["departure"] and not inside:
                raise ValueError(f"{part['id']} note {note['pitch']} left the collection")
            if part["role"] == "keys-progression" and note["pitch"] > VOCAL_CEILING:
                raise ValueError(f"{part['id']} climbed into the vocal register {note['pitch']}")


def assert_identities(parts):
    chords = [part for part in parts if part["role"] == "keys-progression"]
    by = {}
    for part in chords:
        by.setdefault(part["study_id"], {})[part["variation"]] = part
    rhythms = {}
    report = []
    for study_id, vars_ in by.items():
        if _sig(vars_["a"]["notes"]) == _sig(vars_["b"]["notes"]):
            raise ValueError(f"{study_id} variations match")
        rhythm = tuple(note["performed_start"] for note in vars_["a"]["notes"])
        if rhythm in rhythms:
            raise ValueError(f"{study_id} rhythm repeats {rhythms[rhythm]}")
        rhythms[rhythm] = study_id
        report.append({"study_id": study_id, "a": len(vars_["a"]["notes"]), "b": len(vars_["b"]["notes"])})
    return {"studies": report, "method": "keys variations differ; variation A attack times are not shared"}


def _study_row(study):
    row = {key: study[key] for key in (
        "id", "slug", "title", "bpm", "tempo_us", "effective_bpm", "bars", "meter", "bar_ticks",
        "tonic", "tonal_reference", "collection_name", "pitch_classes", "departures", "seed",
        "harmonic_intent", "changes", "change_bars", "pitches", "identity", "limitations",
        "spacing", "vocal_ceiling", "stochastic_draws",
    )}
    if "changes_b" in study:
        row["changes_b"] = study["changes_b"]
    return row


def compose():
    catalog_studies = studies()
    parts = []
    for study in catalog_studies:
        for part in BUILDERS[study["id"]](study):
            parts.append(part.finish())
    assert_collections(catalog_studies, parts)
    identity = assert_identities(parts)
    core = [part for part in parts if part["core"]]
    refs = [part for part in parts if not part["core"]]
    if len(core) != 16 or len(refs) != 16:
        raise ValueError((len(core), len(refs)))
    arrangement = {
        "id": "arrangement-preview-s01a",
        "path": "midi/arrangement.mid",
        "format": 1,
        "container_ticks": 8 * BAR,
        "bpm": 74,
        "tempo_us": bpm_to_us(74),
        "meter": "4/4",
        "description": "Study 01 variation A keys with bass guide A. The bass is not inside the keys file. Nothing is written above E5.",
        "tracks": [
            {"name": "Conductor", "source_part": None, "channel": None},
            {"name": "Keys Progression", "source_part": "s01.keys.a", "channel": 0},
            {"name": "Bass Guide", "source_part": "s01.bass.a", "channel": 1},
        ],
    }
    catalog = {
        "pack_id": PACK_ID, "pack_name": PACK_NAME,
        "catalog_version": GENERATOR_VERSION, "generator_version": GENERATOR_VERSION,
        "ppq": PPQ, "meter": {"numerator": 4, "denominator": 4, "bar_ticks": BAR},
        "pitched_range": [28, VOCAL_CEILING], "c4": 60, "vocal_ceiling": VOCAL_CEILING,
        "note_policy": "note-only MIDI. Pedal, slides, and a sung melody are not encoded.",
        "microtiming": "offset is 0; performed_start = nominal_start",
        "stochastic_draws": 0,
        "seed_meaning": "Seeds identify studies. Nothing is random.",
        "core_part_count": len(core), "reference_part_count": len(refs),
        "range_statement": "Keys stay between MIDI 48 and 76, E5, at most four notes. That ceiling is the room for a vocal. Bass guides are monophonic, MIDI 28 to 52, and are not part of the core count.",
        "studies": [_study_row(study) for study in catalog_studies],
        "parts": [{
            "id": part["id"], "study_id": part["study_id"], "role": part["role"], "variation": part["variation"],
            "core": part["core"], "channel": part["channel"], "path": part["path"], "notes": len(part["notes"]),
            "container_bars": part["container_bars"], "bpm": part["bpm"], "monophonic": part["monophonic"],
        } for part in parts],
        "arrangement": arrangement,
        "preview_part_ids": ["s01.keys.a", "s01.bass.a"],
        "stack_warning": "Use either the combined arrangement or the separate parts. Do not stack the part files on top of the combined file.",
    }
    score = {
        "pack_id": PACK_ID, "generator_version": GENERATOR_VERSION, "ppq": PPQ,
        "parts": parts, "arrangement": arrangement, "identity_check": identity,
    }
    return {"catalog": catalog, "score": score}
