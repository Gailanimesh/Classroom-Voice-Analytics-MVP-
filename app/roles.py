"""
Step 4: map anonymous speaker labels (SPEAKER_00, SPEAKER_01) to Teacher/Student.

Heuristic used: whoever has the most total talk time across the recording is
the Teacher. This is explicitly the kind of approximation the assignment
brief allows ("Teacher vs Student speech (approximation is acceptable)").

IMPORTANT: takes the RAW speaker_turns from diarize_audio(), not the
Whisper-aligned transcript. Overlapping/simultaneous speech (e.g. several
students answering "yes" together) can be correctly detected by diarization
as a speaker turn, but never get its own distinct Whisper text segment —
so talk time must be measured from diarization directly, not from text.
"""


def assign_teacher_student(speaker_turns):
    talk_time = {}
    for turn in speaker_turns:
        dur = turn["end"] - turn["start"]
        talk_time[turn["speaker"]] = talk_time.get(turn["speaker"], 0) + dur

    if not talk_time:
        return {}

    teacher_speaker = max(talk_time, key=talk_time.get)
    return {spk: ("Teacher" if spk == teacher_speaker else "Student") for spk in talk_time}