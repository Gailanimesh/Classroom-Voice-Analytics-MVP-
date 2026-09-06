"""
Step 5: turn the role-tagged transcript into the required metrics.

Question markers are ENGLISH-first, because transcribe.py uses Whisper's
task="translate", which outputs English text regardless of spoken language.
Hindi/Devanagari tokens are kept only as a defensive fallback for rare
untranslated/code-switched words.

Talk-time and interaction metrics come from RAW diarization turns, not the
Whisper-aligned transcript, so a speaker's time counts even when Whisper
never transcribed words for it (e.g. brief overlapping speech).
"""

QUESTION_MARKERS = [
    "?", "what", "why", "how", "when", "who", "where", "which",
    "do you", "can you", "did you", "will you", "is it", "are you",
    "kya", "kaise", "kyun", "kaun", "kab", "kahan",
    "क्या", "कैसे", "क्यों", "कौन", "कब", "कहाँ",
]


def compute_metrics(speaker_turns, aligned_segments, role_map):
    total_time = sum(t["end"] - t["start"] for t in speaker_turns)
    teacher_time = sum(
        t["end"] - t["start"] for t in speaker_turns if role_map.get(t["speaker"]) == "Teacher"
    )
    student_time = total_time - teacher_time

    sorted_turns = sorted(speaker_turns, key=lambda t: t["start"])
    interactions = 0
    prev_speaker = None
    for t in sorted_turns:
        if prev_speaker is not None and t["speaker"] != prev_speaker:
            interactions += 1
        prev_speaker = t["speaker"]

    student_turn_count = sum(1 for t in speaker_turns if role_map.get(t["speaker"]) == "Student")

    teacher_questions = sum(
        1 for s in aligned_segments
        if role_map.get(s["speaker"]) == "Teacher"
        and any(m in s["text"].lower() for m in QUESTION_MARKERS)
    )

    return {
        "teacher_dominance_ratio": round(teacher_time / total_time, 2) if total_time else 0,
        "student_participation_indicator": round(student_time / total_time, 2) if total_time else 0,
        "interaction_count": interactions,
        "teacher_questions": teacher_questions,
        "student_response_count": student_turn_count,
        "teacher_talk_time_sec": round(teacher_time, 1),
        "student_talk_time_sec": round(student_time, 1),
        "total_duration_sec": round(total_time, 1),
    }