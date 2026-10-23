"""
Base Audio Deepfake Detection Backend
======================================
Defines the abstract interface for all audio deepfake detectors in FraudShield.
Handles:
  - Acoustic normalization (DC offset removal + peak scaling)
  - Silence detection (RMS threshold check to prevent false positives and zero division)
  - Chunking for arbitrary-length audio files (including clips > 10 seconds)
  - Short clip safe padding
  - Robust exception handling for unreadable or corrupted audio
  - Calibrated consensus blending and timeline generation
"""
import os
import gc
import abc
import numpy as np
import librosa
import torch
from typing import Optional, List, Dict, Any

from src.config import get_threshold, get_audio_config

KNOWN_FINFLUENCER_NAMES = [
    "nithin kamath", "nikhil kamath", "ankur warikoo", "radhakishan damani",
    "jhunjhunwala", "akshat shrivastava", "rachana ranade", "pranjal kamra",
    "sunil singhania", "saurabh mukherjea", "vijay kedia", "porinju veliyath"
]

def check_finfluencer_impersonation(transcript: str, max_audio_fake_score: float) -> dict:
    """
    Checks if a high-profile financial personality is named in the transcript
    combined with an elevated synthetic audio score, indicating a voice clone impersonation scam.
    Threshold read from config: thresholds.impersonation_audio_threshold
    """
    impersonation_thresh = get_threshold("impersonation_audio_threshold", 0.45)
    if not transcript:
        return {"is_impersonation": False, "target": None}
        
    t_lower = transcript.lower()
    for name in KNOWN_FINFLUENCER_NAMES:
        if name in t_lower:
            if max_audio_fake_score > impersonation_thresh:
                return {
                    "is_impersonation": True,
                    "target": name.title(),
                    "warning": f"Potential AI Voice Clone Impersonation of '{name.title()}' (Voice Spoof Confidence: {max_audio_fake_score*100:.1f}%)"
                }
            else:
                return {
                    "is_impersonation": False,
                    "target": name.title(),
                    "warning": None
                }
    return {"is_impersonation": False, "target": None}


class BaseAudioBackend(abc.ABC):
    """Abstract Base Class for audio deepfake detection backends."""

    def __init__(self, name: str, model_id: str, device: str = "cpu", threshold: float = 0.5):
        self.name = name
        self.model_id = model_id
        self.device = device
        self.threshold = threshold

    @abc.abstractmethod
    def predict_chunk(self, chunk: np.ndarray, sample_rate: int = 16000) -> float:
        """
        Runs model inference on a single audio chunk (1D float32 numpy array).
        Returns:
            float: Synthetic/spoof probability strictly clamped between 0.0 and 1.0.
        """
        raise NotImplementedError

    def _validate_chunk_acoustics(
        self,
        chunk: np.ndarray,
        raw_prob: float,
        sample_rate: int = 16000,
        job_id: str = "",
        time_range: tuple = (0.0, 0.0),
    ) -> float:
        """
        Cross-validates an elevated chunk deepfake score against physical vocal tract invariants.
        Human vocal cords produce natural micro-jitter (typically >= 0.014) and continuous pitch
        inflection (F0 std >= 12.0 Hz). Synthetic neural vocoders (ElevenLabs, Kokoro, HiFi-GAN) exhibit
        mathematically smooth periodicity (jitter < 0.008) or robotic pitch flatness.

        If Wav2Vec2 reports high fake probability (> 0.35), but acoustic analysis verifies the chunk
        possesses unequivocal organic human vocal micro-jitter with zero vocoder indicators, the score
        is attenuated to prevent out-of-domain false positives (e.g., from Indian English accents,
        chunk-boundary breathing, ambient room acoustics, or WhatsApp lossy compression).
        """
        if raw_prob <= 0.35 or chunk is None or len(chunk) < int(0.5 * sample_rate):
            return raw_prob

        try:
            from src.stages.audio_backends.acoustic_forensics import analyze_acoustic_forensics
            ac = analyze_acoustic_forensics(chunk, sample_rate=sample_rate)
            jitter = float(ac.get("jitter", 0.0))
            pitch_std = float(ac.get("pitch_std", 0.0))
            synth_score = float(ac.get("synthetic_score", 0.0))
            indicators = ac.get("indicators", [])

            # Case A: Strong biological vocal fold micro-instability and pitch dynamics with 0 vocoder markers
            if jitter >= 0.014 and pitch_std >= 12.0 and synth_score <= 0.12 and len(indicators) == 0:
                attenuated = round(raw_prob * 0.05, 4)
                print(
                    f"[{job_id}] [{self.name}] Attenuated out-of-domain false positive at {time_range[0]}s-{time_range[1]}s: "
                    f"RAW={raw_prob:.4f} -> {attenuated:.4f} (Human vocal tract: Jitter={jitter:.4f}, PitchStd={pitch_std:.1f})"
                )
                return attenuated

            # Case B: High micro-jitter with calm pitch (e.g. calm speaking with high organic vocal jitter >= 0.018)
            if jitter >= 0.018 and synth_score <= 0.08 and len(indicators) == 0:
                attenuated = round(raw_prob * 0.08, 4)
                print(
                    f"[{job_id}] [{self.name}] Attenuated vocal artifact at {time_range[0]}s-{time_range[1]}s: "
                    f"RAW={raw_prob:.4f} -> {attenuated:.4f} (High micro-jitter={jitter:.4f})"
                )
                return attenuated

        except Exception:
            pass

        return raw_prob

    def process_audio(
        self,
        audio_path: str,
        job_id: str = "audio-job",
        transcript: str = "",
        chunk_duration: Optional[float] = None,
        consensus_weight: Optional[float] = None,
        consensus_min_chunks: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Processes full audio recording through chunking, acoustic normalization,
        inference, and consensus scoring.
        Handles clips longer than 10 seconds, short clips, silent clips, and malformed files safely.
        """
        audio_cfg = get_audio_config()
        if chunk_duration is None:
            chunk_duration = float(audio_cfg.get("chunk_duration_seconds", 5.0))
        if consensus_weight is None:
            consensus_weight = float(audio_cfg.get("consensus_top_weight", 0.65))
        if consensus_min_chunks is None:
            consensus_min_chunks = int(audio_cfg.get("consensus_min_chunks", 2))

        segment_flag_thresh = get_threshold("audio_segment_flag_threshold", 0.45)
        target_sr = 16000

        result: Dict[str, Any] = {
            "avg_score": 0.0,
            "max_score": 0.0,
            "raw_peak_score": 0.0,
            "flagged_segments": [],
            "all_segments": [],
            "impersonation_check": {"is_impersonation": False, "target": None},
            "model_backend": self.name,
            "model_id": self.model_id,
            "revision": getattr(self, "revision", None),
        }

        if not audio_path or not os.path.exists(audio_path):
            print(f"[{job_id}] [{self.name}] Audio path missing or does not exist: {audio_path}")
            result["status"] = "error"
            result["error"] = "File not found"
            return result

        # 1. Safe audio decoding
        try:
            audio, sr = librosa.load(audio_path, sr=target_sr)
        except Exception as load_exc:
            print(f"[{job_id}] [{self.name}] Failed to decode audio file ({audio_path}): {load_exc}")
            result["status"] = "error"
            result["error"] = f"Decoding failed: {load_exc}"
            return result

        audio = np.asarray(audio, dtype=np.float32)

        # 2. Silence & Energy check (RMS < 0.001 or peak < 1e-5)
        rms = float(np.sqrt(np.mean(np.square(audio)))) if len(audio) > 0 else 0.0
        if len(audio) == 0 or rms < 0.001 or np.max(np.abs(audio)) < 1e-5:
            print(f"[{job_id}] [{self.name}] Audio is silent (RMS={rms:.6f}). Returning 0.0 spoof score.")
            result["is_silent"] = True
            result["impersonation_check"] = check_finfluencer_impersonation(transcript, 0.0)
            return result

        # 3. Acoustic Normalization (DC offset removal + Peak scaling)
        audio = audio - np.mean(audio)
        peak = float(np.max(np.abs(audio)))
        if peak > 0:
            audio = audio / peak

        # 4. Chunking: Handles recordings of any length cleanly without artificial zero-padding
        chunk_samples = int(chunk_duration * target_sr)
        scores: List[float] = []
        max_s = 0.0

        if len(audio) <= chunk_samples:
            # Short recording: single chunk
            chunk = audio
            if len(chunk) < target_sr:
                # Wrap-pad ultra-short clips (<1s) to preserve vocal acoustics rather than flat zero silence
                chunk = np.pad(chunk, (0, target_sr - len(chunk)), "wrap")
            try:
                prob = self.predict_chunk(chunk, sample_rate=target_sr)
                prob = max(0.0, min(1.0, float(prob)))
            except Exception as inf_exc:
                print(f"[{job_id}] [{self.name}] Inference failed on short audio: {inf_exc}")
                prob = 0.0

            prob = self._validate_chunk_acoustics(
                chunk, prob, sample_rate=target_sr, job_id=job_id, time_range=(0.0, round(len(audio) / target_sr, 2))
            )
            scores.append(prob)
            max_s = prob
            segment_info = {
                "start": 0.0,
                "end": round(len(audio) / target_sr, 2),
                "score": round(prob, 4),
            }
            result["all_segments"].append(segment_info)
            if prob > segment_flag_thresh:
                result["flagged_segments"].append(segment_info)
        else:
            # Multi-chunk recording (> chunk_duration seconds)
            # 1. Process all full non-overlapping windows
            total_samples = len(audio)
            last_full_end = 0

            for i in range(0, total_samples, chunk_samples):
                if i + chunk_samples <= total_samples:
                    chunk = audio[i:i + chunk_samples]
                    last_full_end = i + chunk_samples
                    start_time = round(i / target_sr, 2)
                    end_time = round(last_full_end / target_sr, 2)

                    try:
                        prob = self.predict_chunk(chunk, sample_rate=target_sr)
                        prob = max(0.0, min(1.0, float(prob)))
                    except Exception as inf_exc:
                        print(f"[{job_id}] [{self.name}] Inference failed on chunk at sample {i}: {inf_exc}")
                        prob = 0.0

                    prob = self._validate_chunk_acoustics(
                        chunk, prob, sample_rate=target_sr, job_id=job_id, time_range=(start_time, end_time)
                    )
                    scores.append(prob)
                    segment_info = {
                        "start": start_time,
                        "end": end_time,
                        "score": round(prob, 4),
                    }
                    result["all_segments"].append(segment_info)

                    if prob > segment_flag_thresh:
                        result["flagged_segments"].append(segment_info)

                    if prob > max_s:
                        max_s = prob

            # 2. Check trailing tail after the last full window
            tail_len = total_samples - last_full_end
            if tail_len > 0:
                if tail_len >= int(1.0 * target_sr):
                    # Sufficient speech in tail (>= 1.0s): evaluate full context window ending at total_samples
                    # with full natural acoustic context (no zero padding)
                    tail_chunk = audio[-chunk_samples:]
                    tail_start = round((total_samples - chunk_samples) / target_sr, 2)
                    tail_end = round(total_samples / target_sr, 2)

                    try:
                        tail_prob = self.predict_chunk(tail_chunk, sample_rate=target_sr)
                        tail_prob = max(0.0, min(1.0, float(tail_prob)))
                    except Exception as inf_exc:
                        print(f"[{job_id}] [{self.name}] Inference failed on tail chunk: {inf_exc}")
                        tail_prob = 0.0

                    tail_prob = self._validate_chunk_acoustics(
                        tail_chunk, tail_prob, sample_rate=target_sr, job_id=job_id, time_range=(tail_start, tail_end)
                    )
                    scores.append(tail_prob)
                    segment_info = {
                        "start": tail_start,
                        "end": tail_end,
                        "score": round(tail_prob, 4),
                    }
                    result["all_segments"].append(segment_info)

                    if tail_prob > segment_flag_thresh:
                        result["flagged_segments"].append(segment_info)

                    if tail_prob > max_s:
                        max_s = tail_prob
                else:
                    # Very short trailing scrap (< 1.0s) like container cutoff or trailing breath.
                    # Extend preceding chunk's display boundary to the true audio end without creating
                    # an artificial zero-padded artifact segment.
                    if result["all_segments"]:
                        result["all_segments"][-1]["end"] = round(total_samples / target_sr, 2)

        # 5. Consensus Scoring & Output assembly
        if scores:
            scores_sorted = sorted(scores, reverse=True)
            k = min(2, len(scores_sorted))
            top_k_mean = float(np.mean(scores_sorted[:k]))
            anti_weight = round(1.0 - consensus_weight, 4)
            consensus_audio = (
                float(consensus_weight * top_k_mean + anti_weight * max_s)
                if len(scores) >= consensus_min_chunks
                else float(max_s)
            )

            # Injected Audio Spoof Detection:
            # If an audio segment demonstrates unequivocal synthetic voice (>0.85),
            # check whether it is a genuine sustained injection or an isolated artifact.
            # Real spliced voice clones typically span >= 2 chunks, have high average score,
            # or appear in short recordings (<= 2 chunks).
            # An isolated single-chunk spike in a long multi-chunk recording where all other
            # segments are bona fide human speech is smoothly attenuated by consensus blending.
            is_corroborated_injection = False
            if max_s >= 0.85:
                if len(scores) <= 2:
                    is_corroborated_injection = True
                elif len(scores_sorted) >= 2 and scores_sorted[1] >= 0.50:
                    is_corroborated_injection = True
                elif float(np.mean(scores)) >= 0.35:
                    is_corroborated_injection = True
                elif max_s >= 0.95 and top_k_mean >= 0.50:
                    is_corroborated_injection = True

            if is_corroborated_injection:
                final_audio_score = float(max_s)
            else:
                final_audio_score = float(consensus_audio)

            result["avg_score"] = round(float(np.mean(scores)), 4)
            result["max_score"] = round(final_audio_score, 4)
            result["raw_peak_score"] = round(float(max_s), 4)

        result["impersonation_check"] = check_finfluencer_impersonation(transcript, result["max_score"])
        return result
