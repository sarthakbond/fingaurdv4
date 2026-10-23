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

    # Calibrated Neural TTS Forensics (ElevenLabs, Gemini Voice, Kokoro vs Bona Fide Human):
    # Prevents false alarms on mobile recordings (WhatsApp/AAC/Opus codecs & calm human voices).
    # Requires multi-signal conjunction: real human vocal cords exhibit natural micro-jitter (>0.015),
    # while neural vocoders synthesize unnaturally smooth mathematical periodicity.
    indicators = []
    suspicious_signals = 0
    signal_weights = []

    # Signal 1: Ultra-low vocal fold micro-jitter (Neural vocoder signature: jitter < 0.010)
    # Real human speech typically has jitter in the 0.015 - 0.050 range.
    has_human_jitter = False
    if len(voiced_f0) > 25:
        if jitter < 0.008:
            suspicious_signals += 1
            signal_weights.append(0.85)
            indicators.append(f"Unnatural vocal fold periodicity (ultra-low micro-jitter: {jitter:.4f})")
        elif jitter < 0.012:
            signal_weights.append(0.35)
        elif jitter > 0.020:
            # Strong natural vocal cord micro-instability confirms bona fide human voice
            has_human_jitter = True

    # Signal 2: Unnatural pitch monotonicity (robotic flat intonation: F0 std < 12.0 Hz)
    # Calm explanatory human speech commonly ranges from 18 - 30 Hz std.
    if len(voiced_f0) > 25:
        if pitch_std < 11.0:
            suspicious_signals += 1
            signal_weights.append(0.80)
            indicators.append(f"Robotic pitch monotonicity (F0 std: {pitch_std:.1f} Hz)")
        elif pitch_std < 14.0:
            signal_weights.append(0.30)

    # Signal 3: Digital silence / unnatural absence of room noise floor in pauses (< 0.0008)
    # Natural phone recordings have room reverb or mic noise floor > 0.005.
    if unvoiced_energy > 0 and unvoiced_energy < 0.0008:
        suspicious_signals += 1
        signal_weights.append(0.70)
        indicators.append("Digital mathematical silence in speech pauses (no ambient room acoustics)")

    # Signal 4: Artificial spectral cutoff only when paired with synthetic isolation
    # Note: Mobile codecs (Opus/AMR/AAC) naturally roll off around 3.0-3.4 kHz, so rolloff
    # is NEVER treated as suspicious on its own without concurring vocoder jitter/silence.
    if rolloff_85 < 2900.0 and suspicious_signals >= 1:
        suspicious_signals += 1
        signal_weights.append(0.60)
        indicators.append(f"Steep vocoder anti-aliasing cutoff (rolloff: {rolloff_85:.0f} Hz)")

    # Multi-signal conjunction fusion:
    # Requires at least 2 concurring suspicious anomalies to reach moderate suspicion,
    # and 3 concurring anomalies for high confidence neural TTS.
    # Biological vocal micro-jitter (>0.020) physically disproves neural vocoder generation.
    if has_human_jitter:
        suspicious_signals = max(0, suspicious_signals - 1)

    if has_human_jitter and suspicious_signals < 3:
        # Physical biological vocal fold instability guarantees natural human acoustics
        synthetic_score = 0.02
        indicators = []
    elif suspicious_signals >= 3:
        synthetic_score = float(np.clip(np.mean([w for w in signal_weights if w > 0]), 0.75, 0.95))
    elif suspicious_signals == 2:
        synthetic_score = float(np.clip(np.mean([w for w in signal_weights if w > 0]), 0.35, 0.50))
    elif suspicious_signals == 1:
        synthetic_score = float(np.clip(max(signal_weights) * 0.35, 0.10, 0.25))
    else:
        # Isolated single codec effects or natural human vocal flutter -> authentic
        synthetic_score = 0.02

    return {
        "synthetic_score": round(synthetic_score, 4),
        "jitter": round(jitter, 5),
        "pitch_std": round(pitch_std, 2),
        "rolloff_85": round(rolloff_85, 1),
        "spectral_flatness": round(flatness, 6),
        "unvoiced_noise_floor": round(unvoiced_energy, 6),
        "indicators": indicators
    }
