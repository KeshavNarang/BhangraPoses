"""
align_video.py

Plug-in replacement for your existing alignment code.
Uses MFCC + cross-correlation for audio alignment.

Dependencies:
    pip install moviepy librosa numpy scipy
"""

import os
import numpy as np
import librosa
from scipy.signal import correlate
from moviepy.editor import VideoFileClip

# -----------------------------
# Config
# -----------------------------
SAMPLE_RATE = 22050
N_MFCC = 13
HOP_LENGTH = 512
MAX_ALLOWED_OFFSET = 60  # seconds, sanity cap

# -----------------------------
# Audio utilities
# -----------------------------
def extract_audio(video_path, wav_path, sr=SAMPLE_RATE):
    """Extract audio from video to wav"""
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(wav_path, fps=sr, logger=None)
    clip.close()


def load_mfcc(audio_path, sr=SAMPLE_RATE, n_mfcc=N_MFCC):
    """Load audio and compute MFCCs"""
    audio, sr = librosa.load(audio_path, sr=sr)
    audio, _ = librosa.effects.trim(audio, top_db=30)
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc, hop_length=HOP_LENGTH)
    return mfcc


# -----------------------------
# Alignment logic
# -----------------------------
def find_audio_offset(mfcc_ref, mfcc_user):
    """Cross-correlate reference MFCC with user MFCC to find best offset"""
    ref_signal = mfcc_ref.mean(axis=0)
    user_signal = mfcc_user.mean(axis=0)

    corr = correlate(user_signal, ref_signal, mode="valid")
    best_frame = np.argmax(corr)
    offset_seconds = best_frame * HOP_LENGTH / SAMPLE_RATE
    confidence = corr[best_frame] / np.mean(corr)

    return offset_seconds, confidence


# -----------------------------
# Video trimming
# -----------------------------
def trim_video(input_video, start_time, output_video):
    clip = VideoFileClip(input_video)
    trimmed = clip.subclip(start_time)
    trimmed.write_videofile(output_video, codec="libx264", audio_codec="aac", logger=None)
    clip.close()
    trimmed.close()


# -----------------------------
# Main function called by Flask
# -----------------------------
def main(reference_video, user_video, output_video):
    ref_audio = "ref_tmp.wav"
    user_audio = "user_tmp.wav"

    # Extract audio
    extract_audio(reference_video, ref_audio)
    extract_audio(user_video, user_audio)

    # Compute MFCCs
    mfcc_ref = load_mfcc(ref_audio)
    mfcc_user = load_mfcc(user_audio)

    # Find offset
    offset_seconds, confidence = find_audio_offset(mfcc_ref, mfcc_user)
    print(f"Offset: {offset_seconds:.2f}s")
    print(f"Confidence: {confidence:.2f}")

    if offset_seconds < 0 or offset_seconds > MAX_ALLOWED_OFFSET:
        raise RuntimeError(
            f"Alignment offset {offset_seconds:.2f}s is implausible. Likely matched wrong section."
        )

    # Trim video
    trim_video(user_video, offset_seconds, output_video)

    # Clean up
    os.remove(ref_audio)
    os.remove(user_audio)
