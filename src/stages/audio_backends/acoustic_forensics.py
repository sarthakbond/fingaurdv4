"""
Acoustic Forensics & Neural TTS Detector
=========================================
Analyzes acoustic properties that distinguish modern neural text-to-speech
(e.g., Google Gemini 1.1 Flash, ElevenLabs, OpenAI Voice, Kokoro) from natural
human vocal cord acoustics:

1. Pitch (F0) Micro-Jitter: Human vocal folds have natural biological micro-instability
   (jitter 0.5% - 2.5%). Neural vocoders generate mathematically smooth trajectories
   or low-variance F0 transitions.
2. Spectral Flatness & Bandwidth Rolloff: Modern fast neural TTS often exhibits
   specific vocoder anti-aliasing cutoffs and lower spectral entropy in voiced phonemes.
3. Silence & Background Noise Floor: Human recordings possess ambient acoustic noise,
   whereas synthesized audio features unnatural digital silence or uniform dithering.
"""
import numpy as np
import librosa
from typing import Dict, Any

def analyze_acoustic_forensics(audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
    """
    Analyzes an audio waveform for modern neural TTS acoustic artifacts.

    Returns:
        dict: {
            "synthetic_score": float,  # [0.0, 1.0] higher = more likely synthetic TTS
            "jitter": float,
            "pitch_std": float,
            "rolloff_85": float,
            "spectral_flatness": float,
            "indicators": list[str]
        }
    """
    indicators = []
    synthetic_score = 0.0

    if audio is None or len(audio) < sample_rate * 0.5:
        return {
            "synthetic_score": 0.0,
            "jitter": 0.0,
            "pitch_std": 0.0,
            "rolloff_85": 0.0,
            "spectral_flatness": 0.0,
            "indicators": []
        }

    # Ensure float32
    audio = np.asarray(audio, dtype=np.float32)

    # 1. Pitch / F0 estimation using librosa.pyin
    try:
        f0, voiced_flag, _ = librosa.pyin(
            audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sample_rate,
            frame_length=1024
        )
        voiced_f0 = f0[voiced_flag & ~np.isnan(f0)] if f0 is not None else []
    except Exception:
        voiced_f0 = []

    jitter = 0.0
    pitch_std = 0.0
    if len(voiced_f0) > 15:
        diffs = np.abs(np.diff(voiced_f0))
        relative_diffs = diffs / np.maximum(voiced_f0[:-1], 1e-4)
        jitter = float(np.mean(relative_diffs))
        pitch_std = float(np.std(voiced_f0))

    # 2. Spectral Rolloff (85% energy percentile)
    try:
        rolloff_85 = float(np.mean(librosa.feature.spectral_rolloff(y=audio, sr=sample_rate, roll_percent=0.85)))
    except Exception:
        rolloff_85 = 4000.0

    # 3. Spectral Flatness
    try:
        flatness = float(np.mean(librosa.feature.spectral_flatness(y=audio)))
    except Exception:
        flatness = 0.05

    # 4. Background noise floor / digital silence in unvoiced intervals
    unvoiced_energy = 0.0
    if f0 is not None and len(f0) > 0:
        unvoiced_frames = ~voiced_flag
        if np.any(unvoiced_frames):
            frame_len = 1024
            hop_len = 256
            rms = librosa.feature.rms(y=audio, frame_length=frame_len, hop_length=hop_len)[0]
            if len(rms) >= len(unvoiced_frames):
                unvoiced_energy = float(np.mean(rms[:len(unvoiced_frames)][unvoiced_frames]))

    # Scoring Heuristics calibrated on Gemini Omni / ElevenLabs vs human benchmarks:
    sub_scores = []

    # Signal A: Low spectral flatness (< 0.040 indicates synthetic harmonic isolation)
    if flatness < 0.038:
        sub_scores.append(0.70)
        indicators.append(f"Synthetic harmonic structure (spectral flatness: {flatness:.4f})")
    elif flatness < 0.045:
        sub_scores.append(0.40)

    # Signal B: Bandwidth cutoff / vocoder compression (rolloff_85 < 3300 Hz)
    if rolloff_85 < 3250.0:
        sub_scores.append(0.75)
        indicators.append(f"Vocoder bandwidth compression (rolloff: {rolloff_85:.0f} Hz)")
    elif rolloff_85 < 3400.0:
        sub_scores.append(0.50)

    # Signal C: Pitch contour smoothness / unnatural intonation
    if len(voiced_f0) > 15:
        if pitch_std < 22.0:
            sub_scores.append(0.65)
            indicators.append(f"Unnatural pitch monotonicity (F0 std: {pitch_std:.1f} Hz)")
        elif pitch_std < 25.0:
            sub_scores.append(0.35)

    # Signal D: Digital silence / low room noise floor in pauses
    if unvoiced_energy > 0 and unvoiced_energy < 0.005:
        sub_scores.append(0.60)
        indicators.append("Near-zero acoustic room noise floor in pauses (digital silence)")

    if sub_scores:
        synthetic_score = float(np.mean(sub_scores))
    else:
        synthetic_score = 0.05

    return {
        "synthetic_score": round(synthetic_score, 4),
        "jitter": round(jitter, 5),
        "pitch_std": round(pitch_std, 2),
        "rolloff_85": round(rolloff_85, 1),
        "spectral_flatness": round(flatness, 6),
        "unvoiced_noise_floor": round(unvoiced_energy, 6),
        "indicators": indicators
    }
