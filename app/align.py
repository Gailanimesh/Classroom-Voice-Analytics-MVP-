"""
Step 3: glue Whisper's transcript segments to pyannote's speaker turns.

Pure Python, no ML here — for each transcript segment, find which speaker
turn overlaps it the most in time.

Uses MAXIMUM OVERLAP rather than midpoint-containment. Midpoint-containment
(checking only whether one specific instant falls inside a turn) can miss a
real second speaker entirely if their turns are short or slightly offset
from Whisper's segment boundaries — the segment's one checked instant
simply never lands inside that speaker's turn, even when real overlap
exists. Overlap-based matching checks the whole segment span against every
turn and picks the best match, which is the standard, more robust approach
for merging ASR output with diarization output.
"""


# def align_transcript_with_speakers(transcript_segments, speaker_turns):
#     aligned = []
#     for seg in transcript_segments:
#         best_speaker = "UNKNOWN"
#         best_overlap = 0.0
#         for turn in speaker_turns:
#             overlap = min(seg["end"], turn["end"]) - max(seg["start"], turn["start"])
#             if overlap > best_overlap:
#                 best_overlap = overlap
#                 best_speaker = turn["speaker"]
#         aligned.append({**seg, "speaker": best_speaker})
#     return aligned

def align_transcript_with_speakers(transcript_segments, speaker_turns):
    aligned = []
    turn_idx = 0
    num_turns = len(speaker_turns)

    for seg in transcript_segments:
        best_speaker = "UNKNOWN"
        best_overlap = 0.0
        while (
            turn_idx < num_turns
            and speaker_turns[turn_idx]["end"] <= seg["start"]
        ):
            turn_idx += 1
        curr = turn_idx
        while curr < num_turns and speaker_turns[curr]["start"] < seg["end"]:
            turn = speaker_turns[curr]
            overlap = min(seg["end"], turn["end"]) - max(
                seg["start"], turn["start"]
            )
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = turn["speaker"]
            curr += 1

        aligned.append({**seg, "speaker": best_speaker})

    return aligned