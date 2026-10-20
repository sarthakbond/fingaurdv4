"""
FinGuard User Dataset & Multi-Modal Verification Suite
======================================================
Automated end-to-end evaluation runner across all user-supplied test videos:
  1. AI Synthetic & Deepfake Videos (ai test video/)
  2. Human Scam / SEBI Violation Videos (huma_test_vid/scam_vid/)
  3. Human Non-Scam / Educational Videos (huma_test_vid/noscam_vid/)

Tests multi-modal detection:
  - Gemini Diamond watermark detection & provenance verification
  - Visual face manipulation (ms-eff-gcvit / deepfake detector)
  - Synthetic audio voice clone detection (wav2vec2)
  - Faster-Whisper Hindi/English/Hinglish speech transcription
  - Ollama Llama 3.1 & heuristic SEBI compliance intent classification
  - SEBI entity verification against registered intermediaries
  - Phishing domain and bio-funnel detection
"""

import os
import sys
import time
import json
import uuid
import shutil
import glob

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.stages.stage1_ingest import run_stage1_ingest
from src.stages.stage2_vision import run_stage2_vision
from src.stages.stage3_audio import run_stage3_audio
from src.stages.stage4_transcription import run_stage4_transcription
from src.stages.stage5_llm import run_stage5_llm
from src.stages.stage6_registry import run_stage6_registry
from src.stages.stage9_apk_domain import scan_text_for_phishing_domains
from src.config import get_vision_threshold, get_threshold

def get_calibrated_verdict(is_deepfake: bool, is_scam: bool, composite_risk: float, registry_verdict: str):
    if is_deepfake and is_scam:
        return "Critical: Deepfake + Scam"
    elif is_deepfake:
        return "Warning: Deepfake Detected"
    elif is_scam:
        return "Warning: SEBI Violation / Scam"
    elif registry_verdict == "name-number mismatch":
        return "Warning: SEBI Violation / Scam"
    elif registry_verdict in ("not found", "malformed number", "uncertain match"):
        return "Suspicious: Review Recommended"
    elif composite_risk >= 0.35:
        return "Suspicious: Review Recommended"
    else:
        return "Safe"

def run_tests():
    temp_base = os.path.join(ROOT_DIR, "temp")
    os.makedirs(temp_base, exist_ok=True)
    tests_out_dir = os.path.join(ROOT_DIR, "tests")
    os.makedirs(tests_out_dir, exist_ok=True)

    test_dirs = [
        {"category": "AI Deepfake Video", "path": os.path.join(ROOT_DIR, "ai test video"), "expected_deepfake": True},
        {"category": "Human Scam Video", "path": os.path.join(ROOT_DIR, "huma_test_vid", "scam_vid"), "expected_deepfake": False, "expected_scam": True},
        {"category": "Human Non-Scam Video", "path": os.path.join(ROOT_DIR, "huma_test_vid", "noscam_vid"), "expected_deepfake": False, "expected_scam": False},
    ]

    all_files = []
    for td in test_dirs:
        pattern = os.path.join(td["path"], "*.mp4")
        found = glob.glob(pattern)
        for f in found:
            all_files.append({
                "category": td["category"],
                "file_path": f,
                "expected_deepfake": td.get("expected_deepfake"),
                "expected_scam": td.get("expected_scam")
            })

    print("================================================================================")
    print(f"  FinGuard Dataset Verification Suite — {len(all_files)} Files Identified")
    print("================================================================================")

    results = []
    v_thresh = get_vision_threshold()
    a_thresh = get_threshold("audio_fake_threshold", 0.5)

    for idx, item in enumerate(all_files, 1):
        file_path = item["file_path"]
        fname = os.path.basename(file_path)
        cat = item["category"]
        job_id = f"test_{uuid.uuid4().hex[:8]}"
        job_temp_dir = os.path.join(temp_base, job_id)
        os.makedirs(job_temp_dir, exist_ok=True)

        print(f"\n[{idx}/{len(all_files)}] [{cat}] {fname}")
        t0 = time.time()

        try:
            # 1. Ingest
            ingest = run_stage1_ingest(file_path, job_temp_dir, job_id)
            ai_wm = ingest.get("ai_watermark", {})
            has_wm = bool(ai_wm.get("watermark_detected"))

            # 2. Vision
            vision = run_stage2_vision(ingest.get("face_frames_paths", []), job_id)
            v_score = vision.get("max_score", 0.0)
            if has_wm:
                v_score = 1.0
                vision["is_deepfake"] = True

            # 4. Transcription
            tx = run_stage4_transcription(ingest.get("audio_path"), job_id)
            transcript = tx.get("transcript", "").strip()

            # 3. Audio
            audio = run_stage3_audio(
                ingest.get("audio_path"),
                job_id,
                transcript=transcript,
                ai_watermark_detected=has_wm,
                vision_score=v_score
            )
            a_score = audio.get("max_score", 0.0)

            # 5. LLM
            llm = run_stage5_llm(transcript, job_id, segments=tx.get("segments", []))

            # 6. Registry
            reg = run_stage6_registry(llm, job_id)

            # 9. Domain
            domain = scan_text_for_phishing_domains(transcript, job_id) if transcript else {}
            has_phish = domain.get("any_phishing", False)

            # Aggregation
            is_deepfake = (v_score > v_thresh) or (a_score > a_thresh) or has_wm
            is_scam = bool(llm.get("is_scam_likely")) or has_phish
            comp_risk = float(llm.get("composite_risk_score", 0.0))
            verdict = get_calibrated_verdict(is_deepfake, is_scam, comp_risk, reg.get("verdict", "not claimed"))
            elapsed = round(time.time() - t0, 2)

            res_entry = {
                "filename": fname,
                "category": cat,
                "verdict": verdict,
                "is_deepfake": is_deepfake,
                "is_scam": is_scam,
                "ai_watermark_detected": has_wm,
                "watermark_details": ai_wm.get("details", "None"),
                "vision_score": round(v_score, 4),
                "audio_score": round(a_score, 4),
                "composite_risk": round(comp_risk, 4),
                "content_intent": llm.get("content_intent"),
                "speaker_stance": llm.get("speaker_stance"),
                "evidence_quotes": {
                    "implied_returns": llm.get("implied_returns", []),
                    "paywall_push": llm.get("paywall_push", []),
                    "credential_misrep": llm.get("credential_misrepresentation", []),
                    "specific_returns": llm.get("specific_return_promises", []),
                },
                "transcript_preview": transcript[:150] + ("..." if len(transcript) > 150 else ""),
                "elapsed_sec": elapsed,
                "status": "success"
            }

            print(f"  -> Verdict: {verdict}")
            print(f"  -> AI Watermark: {has_wm} | Vision Score: {v_score:.2f} | Audio Score: {a_score:.2f}")
            print(f"  -> Intent: {llm.get('content_intent')} | Scam: {is_scam} | Risk: {comp_risk:.2f}")
            if transcript:
                print(f"  -> Transcript ({len(transcript)} chars): \"{transcript[:90]}...\"")
            print(f"  -> Time: {elapsed}s")

        except Exception as e:
            print(f"  -> ERROR: {e}")
            res_entry = {
                "filename": fname,
                "category": cat,
                "verdict": "ERROR",
                "error": str(e),
                "status": "failed"
            }
        finally:
            if os.path.exists(job_temp_dir):
                shutil.rmtree(job_temp_dir, ignore_errors=True)

        results.append(res_entry)

    # Save results
    json_path = os.path.join(tests_out_dir, "user_dataset_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n================================================================================")
    print("  EVALUATION SUMMARY SCORECARD")
    print("================================================================================")
    print(f"{'Filename':<40} | {'Category':<20} | {'Verdict':<28} | {'WM':<5} | {'V-Score':<7} | {'Scam':<5}")
    print("-" * 115)
    for r in results:
        wm_str = "YES" if r.get("ai_watermark_detected") else "NO"
        v_str = f"{r.get('vision_score', 0.0):.2f}"
        scam_str = "YES" if r.get("is_scam") else "NO"
        print(f"{r['filename'][:38]:<40} | {r['category'][:18]:<20} | {r['verdict'][:26]:<28} | {wm_str:<5} | {v_str:<7} | {scam_str:<5}")

    print("================================================================================")
    print(f"Saved complete scorecard to {json_path}")

if __name__ == "__main__":
    run_tests()
