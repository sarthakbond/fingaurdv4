import os
import gc
import torch
import numpy as np
from typing import Optional

from src.config import get_device, get_stage_config, get_threshold, get_audio_config
from src.stages.audio_backends import get_audio_backend, check_finfluencer_impersonation, KNOWN_FINFLUENCER_NAMES


def run_stage3_audio(
    audio_path: str,
    job_id: str,
    transcript: str = "",
    backend_name: Optional[str] = None,
    ai_watermark_detected: bool = False,
    vision_score: float = 0.0
) -> dict:
    """
    Runs audio deepfake detection on the extracted audio with acoustic normalization.
    Combines modular Wav2Vec2 backends with acoustic spectral/pitch forensics
    and multi-modal provenance cues (Gemini diamond watermark).
    Returns:
        dict: {
            "avg_score": float,
            "max_score": float,
            "flagged_segments": list[dict], # Suspicious segments only (>0.45)
            "all_segments": list[dict],     # Full continuous timeline chunks for risk scrubber
            "impersonation_check": dict,
            "acoustic_forensics": dict,
            "model_backend": str,
            "model_id": str
        }
    """
    print(f"[{job_id}] Running Stage 3: Audio Deepfake Detection (Modular Backend & Acoustic Forensics)")
    result = {
        "avg_score": 0.0,
        "max_score": 0.0,
        "raw_peak_score": 0.0,
        "flagged_segments": [],
        "all_segments": [],
        "impersonation_check": {"is_impersonation": False, "target": None}
    }
    
    if not audio_path or not os.path.exists(audio_path):
        print(f"[{job_id}] No audio track provided. Skipping audio stage.")
        return result
        
    try:
        backend = get_audio_backend(backend_name=backend_name)
        result = backend.process_audio(audio_path, job_id=job_id, transcript=transcript)

        # Acoustic Forensics & Neural TTS detection (captures Gemini Omni, ElevenLabs, Kokoro)
        try:
            import librosa
            from src.stages.audio_backends.acoustic_forensics import analyze_acoustic_forensics
            audio_arr, sr = librosa.load(audio_path, sr=16000)
            acoustic = analyze_acoustic_forensics(audio_arr, sample_rate=sr)
            result["acoustic_forensics"] = acoustic
            ac_score = acoustic.get("synthetic_score", 0.0)

            backend_score = float(result.get("max_score", 0.0))
            if ai_watermark_detected:
                # Video is confirmed 100% synthetic (Google Gemini / Veo)
                result["max_score"] = max(backend_score, 0.96)
                result["avg_score"] = max(result.get("avg_score", 0.0), 0.94)
                result["raw_peak_score"] = max(result.get("raw_peak_score", 0.0), 0.96)
                result["forensic_enhancement"] = "gemini_provenance"
                duration_sec = round(len(audio_arr) / float(sr), 2)
                result["flagged_segments"] = [
                    {
                        "start": 0.0,
                        "end": duration_sec,
                        "score": 0.96,
                        "reason": "AI speech generation confirmed via Google Gemini provenance watermark & neural vocoder characteristics"
                    }
                ]
            elif ac_score >= 0.75 and (backend_score > 0.25 or len(acoustic.get("indicators", [])) >= 3):
                # Strong multi-signal Neural TTS detected (ElevenLabs / Kokoro / Gemini Voice)
                result["max_score"] = round(max(backend_score, ac_score), 4)
                result["raw_peak_score"] = round(max(result.get("raw_peak_score", 0.0), ac_score), 4)
                result["forensic_enhancement"] = "acoustic_tts"
                if not result.get("flagged_segments"):
                    duration_sec = round(len(audio_arr) / float(sr), 2)
                    reasons = acoustic.get("indicators", []) or ["Neural vocoder synthesis detected"]
                    result["flagged_segments"] = [
                        {
                            "start": 0.0,
                            "end": duration_sec,
                            "score": round(ac_score, 4),
                            "reason": f"Neural TTS detected: {'; '.join(reasons)}"
                        }
                    ]
            elif (
                not ai_watermark_detected
                and ac_score <= 0.08
                and acoustic.get("jitter", 0.0) >= 0.015
                and len(acoustic.get("indicators", [])) == 0
            ):
                # Whole-recording acoustic analysis verifies bona fide human vocal folds
                if backend_score > 0.25:
                    print(
                        f"[{job_id}] Cross-modal acoustic suppression: Backend score {backend_score:.4f} "
                        f"contradicted by confirmed human vocal tract (Jitter={acoustic.get('jitter'):.4f}, "
                        f"PitchStd={acoustic.get('pitch_std'):.1f}, Synthetic={ac_score}). Attenuating false positive."
                    )
                    result["max_score"] = min(backend_score, 0.15)
                    result["avg_score"] = min(result.get("avg_score", 0.0), 0.10)
                    result["raw_peak_score"] = min(result.get("raw_peak_score", 0.0), 0.15)
                    result["flagged_segments"] = []
                    result["forensic_enhancement"] = "human_vocal_tract_verified"
                else:
                    result["forensic_enhancement"] = None
            elif backend_score < 0.20:
                # Deep learning transformer confirms natural human speech dynamics
                result["forensic_enhancement"] = None
        except Exception as ac_err:
            print(f"[{job_id}] Acoustic forensics non-fatal warning: {ac_err}")

        enh_tag = f" + {result['forensic_enhancement']}" if result.get("forensic_enhancement") else ""
        print(
            f"[{job_id}] Audio complete ({result.get('model_backend')}{enh_tag}). "
            f"Calibrated Score: {result['max_score']:.4f} (Peak: {result.get('raw_peak_score', result['max_score']):.4f}), "
            f"Chunks: {len(result['all_segments'])}, Impersonation: {result['impersonation_check']['is_impersonation']}"
        )
        return result
    except Exception as e:
        print(f"[{job_id}] Audio stage failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        return result
    finally:
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
