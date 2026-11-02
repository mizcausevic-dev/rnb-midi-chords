"""Factual article draft. Not published."""

from __future__ import annotations

from tools.statements import AUDITION, ON_PICTURE, PREVIEW_LINE, PROGRAM, PUBLICATION, WARNING

TITLE = "R&B MIDI Chords is a note-only MIDI study pack"
SUBTITLE = "Eight studies of open voicings, a matched byte check, and a simple-synth preview that is not a master"
TAGS = ["midi", "rnb", "chords", "music-production", "composition"]
TAG_LINE = "Tags: " + ", ".join(TAGS)

PARAGRAPHS = [
    "DRAFT. " + PUBLICATION,
    TAG_LINE,
    "The pack is eight R&B chord studies in 4/4. Each tempo is one integer between 65 and 100 BPM, chosen before the notes. Every study is 8 bars. Each study has two keys variations. That is the core: sixteen files. Each study also has two bass guides. Those sixteen files are not part of the core count, and they are not merged into the keys files. No single progression is offered as the definition of R&B.",
    "Pocket is D natural minor at 74, one chord a bar, with A7 flagged because of C#. Borrowed is C major at 82, and the Ab major and F minor chords leave that key. Pedal is A natural minor at 68. After bar 1 the keys arrive a sixteenth early. Two Register is G major at 90, a shell on beat 1 and a color tone on beat 3. Plagal is Bb major at 78: two bars each of Bbmaj7, Ebmaj7, Ebm, and Bbmaj9. Late Sus is F major at 86 and enters on the second eighth. Space is E natural minor at 70, with keys only on the odd bars. No Tonic is eight shells at 96 and does not land on one key.",
    "Keys stay between MIDI 48 and 76, E5, with at most four notes sounding. That ceiling is the room for a vocal. Bass guides stay between 28 and 52 and are monophonic. C4 is 60. The resolution is 960 ticks per quarter note. Offsets are 0. These studies are original.",
    PROGRAM,
    "The preview synth uses a sine plus a quiet triangle for the keys and a sine for the bass. That mapping is documented. It is not a program change.",
    "The primary preview is study 01, Pocket, variation A, for all 8 bars: the keys file and bass guide A together. At 74 BPM the page records 25.95 seconds. The other studies are in the MIDI and are not in that audio file. "
    + PREVIEW_LINE
    + ". The film takes its audio from that preview file and shows the words "
    + ON_PICTURE
    + " on the picture and in the WebVTT captions.",
    AUDITION
    + " The validator reopened the MIDI bytes and compared them with the canonical score. That is a structural check. The sample peak written beside the preview is the peak of the integer mix. It is not LUFS and it is not a true-peak reading. Nothing in this build is claimed as a master.",
    "The stills are procedural illustrations of open chord spacing, with a pale band left for a vocal. They are not photographs of a session or of performers.",
    "When a public URL exists, use either the combined arrangement or the separate parts. " + WARNING,
    "Call to action: the MIDI, the matched report, and the preview belong together. Do not publish this draft to Medium, Instagram, or X from the draft files alone.",
]


def markdown() -> str:
    body = "\n\n".join(PARAGRAPHS)
    return f"# {TITLE}\n\n{SUBTITLE}\n\n{body}\n"


def plain_text() -> str:
    lines = [TITLE, "", SUBTITLE, "", *PARAGRAPHS, ""]
    return "\n".join(lines) + "\n"
