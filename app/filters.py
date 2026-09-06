"""
Whisper does NOT reliably filter filler words ("umm", "so", "okay", "hmm") —
sometimes it transcribes them, sometimes its internal VAD drops them, and
there's no consistency to rely on. This is a small manual cleanup pass so
your metrics (question counts, word counts) aren't skewed by filler noise.

Not an NLP task — just a lookup-and-strip.
"""

FILLER_WORDS = {
    "umm", "um", "uh", "uhh", "ahh", "ah", "so", "okay", "ok", "hmm", "hm",
    "like", "you know", "basically", "actually",
}


def clean_text(text: str) -> str:
    words = text.strip().split()
    cleaned = [w for w in words if w.lower().strip(",.") not in FILLER_WORDS]
    return " ".join(cleaned)
