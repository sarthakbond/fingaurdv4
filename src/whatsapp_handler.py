"""
FinGuard — WhatsApp Forensic Bot Handler
Connects WhatsApp (via Twilio Webhooks or Cloudflare/Ngrok Tunnel) directly
to FinGuard's 9-stage multimodal forensic engine.
"""

import os
import re
import uuid
import shutil
import requests
import datetime
import numpy as np
from typing import Optional, Dict, Any

from src.config import settings, get_threshold, get_vision_threshold, get_stage_config, get_device
from src.stages.stage1_ingest import run_stage1_ingest
from src.stages.stage2_vision import run_stage2_vision
from src.stages.stage3_audio import run_stage3_audio
from src.stages.stage4_transcription import run_stage4_transcription
from src.stages.stage5_llm import run_stage5_llm
from src.stages.stage6_registry import run_stage6_registry
from src.stages.stage7_ocr import run_stage7_ocr, run_video_keyframes_ocr
from src.stages.stage8_report import generate_sebi_scores_complaint
from src.stages.stage9_apk_domain import run_stage9_apk_domain, scan_domain

from twilio.twiml.messaging_response import MessagingResponse

# ── XML / TwiML Helpers ────────────────────────────────────────────────────────

def build_twiml_response(body: str) -> str:
    """Uses official Twilio MessagingResponse to generate compliant TwiML."""
    resp = MessagingResponse()
    resp.message(body)
    return str(resp)

# ── Outbound Twilio WhatsApp Sender ───────────────────────────────────────────

def send_twilio_message(to_number: str, body: str, from_number: Optional[str] = None) -> bool:
    """
    Sends an outbound WhatsApp message via Twilio REST API.
    Used for asynchronous background delivery (e.g. video processing).
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    default_from = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    sender = from_number or default_from

    if not account_sid or not auth_token:
        print("[WhatsApp] Warning: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set; skipping outbound REST API send.")
        return False

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    data = {
        "To": to_number,
        "From": sender,
        "Body": body
    }

    try:
        resp = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=20)
        if resp.status_code in [200, 201]:
            print(f"[WhatsApp] Successfully sent outbound message to {to_number}")
            return True
        else:
            print(f"[WhatsApp] Twilio outbound failed ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        print(f"[WhatsApp] Error sending outbound Twilio message: {e}")
        return False

# ── Media Downloader ──────────────────────────────────────────────────────────

def download_twilio_media(media_url: str, dest_path: str, timeout: int = 60) -> bool:
    """
    Downloads media attached to a Twilio WhatsApp message.
    Uses Twilio HTTP Basic Auth if credentials are configured.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    auth = (account_sid, auth_token) if (account_sid and auth_token) else None

    try:
        print(f"[WhatsApp] Downloading media from {media_url}...")
        resp = requests.get(media_url, auth=auth, stream=True, timeout=timeout)
        if resp.status_code == 200:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"[WhatsApp] Saved media to {dest_path} ({os.path.getsize(dest_path)} bytes)")
            return True
        else:
            print(f"[WhatsApp] Failed to download media: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"[WhatsApp] Exception downloading media: {e}")
        return False

# ── Message Formatting ────────────────────────────────────────────────────────

def format_whatsapp_verdict_card(
    verdict: str,
    composite_risk: float,
    scan_type: str,
    evidence_breakdown: Optional[dict] = None,
    sebi_analysis: Optional[dict] = None,
    registry_check: Optional[dict] = None,
    vision_score: Optional[float] = None,
    audio_score: Optional[float] = None,
    ai_watermark: Optional[dict] = None,
    domain_scan: Optional[dict] = None,
    apk_result: Optional[dict] = None,
    job_id: Optional[str] = None,
    public_url: Optional[str] = None
) -> str:
    """
    Formats the forensic analysis into an intuitive, high-visibility WhatsApp card.
    Uses WhatsApp markdown formatting (*bold*, _italics_, bullet points).
    """
    # 1. Headline badge & icon
    verdict_lower = verdict.lower()
    if "critical" in verdict_lower:
        badge = "🚨 *CRITICAL: DEEPFAKE + SCAM*"
    elif "warning" in verdict_lower and "deepfake" in verdict_lower:
        badge = "⚠️ *WARNING: DEEPFAKE DETECTED*"
    elif "warning" in verdict_lower:
        badge = "⚠️ *WARNING: SEBI VIOLATION / SCAM*"
    elif "suspicious" in verdict_lower:
        badge = "⚠️ *SUSPICIOUS: REVIEW RECOMMENDED*"
    elif "safe" in verdict_lower:
        badge = "✅ *SAFE: NO FRAUD DETECTED*"
    else:
        badge = f"🔍 *{verdict.upper()}*"

    pct = int(round(composite_risk * 100))
    risk_bar = f"*{pct}% Risk Likelihood*"

    lines = [
        "🛡️ *FinGuard Forensic Alert*",
        "━━━━━━━━━━━━━━━━━━━━",
        f"*Verdict:* {badge}",
        f"*Risk Rating:* {risk_bar}",
        f"*Scan Type:* {scan_type.title()}",
        "",
        "📊 *Forensic Breakdown:*"
    ]

    # Visual Forensics
    if ai_watermark and ai_watermark.get("watermark_detected"):
        lines.append(f"• *Visual Provenance:* ⚠️ AI Watermark Verified ({ai_watermark.get('details', 'Synthetic AI')})")
    elif vision_score is not None:
        v_thresh = get_vision_threshold()
        if vision_score > v_thresh:
            lines.append(f"• *Visual Authenticity:* ⚠️ Synthetic Deepfake Artifacts (Score: {vision_score:.2f})")
        else:
            lines.append(f"• *Visual Authenticity:* ✅ Authentic Camera Capture (Score: {vision_score:.2f})")

    # Audio Forensics
    if audio_score is not None:
        a_thresh = get_threshold("audio_fake_threshold", 0.5)
        if audio_score > a_thresh:
            lines.append(f"• *Voice Cloning Check:* ⚠️ Synthetic Voice Clone Detected (Score: {audio_score:.2f})")
        else:
            lines.append(f"• *Voice Cloning Check:* ✅ Authentic Natural Voice (Score: {audio_score:.2f})")

    # SEBI Registry Check
    if registry_check:
        reg_v = registry_check.get("verdict", "not claimed").lower()
        if reg_v == "verified":
            entity = registry_check.get("matched_entity", {}).get("name", "Registered Entity")
            lines.append(f"• *SEBI Registry:* ✅ Verified SEBI Registered ({entity})")
        elif reg_v == "name-number mismatch":
            lines.append("• *SEBI Registry:* ❌ Impersonation Alert (Registration belongs to another entity)")
        elif reg_v in ["not found", "malformed number"]:
            lines.append("• *SEBI Registry:* ❌ Unregistered Entity (No matching SEBI registration found)")
        elif reg_v == "not claimed":
            lines.append("• *SEBI Registry:* ℹ️ No SEBI registration claimed")

    # Phishing / Domain Scan
    if domain_scan and domain_scan.get("domain"):
        dom = domain_scan.get("domain")
        if domain_scan.get("is_phishing"):
            reason = domain_scan.get("reason", "Typo-squatting / Fake Broker")
            lines.append(f"• *Domain Safety:* 🚨 Phishing / Fake Broker URL ({dom} - {reason})")
        else:
            lines.append(f"• *Domain Safety:* ✅ Whitelisted / Clean URL ({dom})")

    # APK Check
    if apk_result:
        if apk_result.get("is_suspicious"):
            reason = apk_result.get("reason", "Dangerous trojan permissions detected")
            lines.append(f"• *APK Analysis:* 🚨 Suspicious / Malicious APK ({reason})")
        else:
            lines.append("• *APK Analysis:* ✅ Whitelisted official broker package")

    # Key Detected Signals
    signals = []
    if sebi_analysis:
        if sebi_analysis.get("hinglish_slang_detected"):
            slangs = sebi_analysis["hinglish_slang_detected"]
            slang_str = ", ".join(f'"{s}"' for s in slangs[:3])
            signals.append(f"Scam slang detected: {slang_str}")
        if sebi_analysis.get("specific_return_promises"):
            proms = sebi_analysis["specific_return_promises"]
            signals.append(f"Unrealistic return promises: {proms[0] if isinstance(proms, list) else proms}")
        if sebi_analysis.get("urgency_scarcity_language"):
            signals.append("High-pressure urgency tactics detected")
        if sebi_analysis.get("fee_or_transfer_requests"):
            signals.append("Suspicious upfront fee / fund transfer request")
        if sebi_analysis.get("credential_or_otp_requests"):
            signals.append("Dangerous credential / OTP request")
        if sebi_analysis.get("paywall_push"):
            signals.append("Unlawful VIP / private paid channel solicitation")

    if signals:
        lines.append("")
        lines.append("🚨 *Detected Warning Flags:*")
        for s in signals[:4]:
            lines.append(f"• {s}")

    # Protective Advice
    lines.append("")
    if "safe" in verdict_lower:
        lines.append("💡 *Guidance:* No scam signatures found. Always ensure you only act on advice from SEBI-registered Research Analysts.")
    else:
        lines.append("⛔ *Action Advised:*")
        lines.append("• Do NOT transfer money or share UPI IDs/OTPs.")
        lines.append("• Do NOT join private VIP Telegram/WhatsApp groups.")
        lines.append("• Verify any advisor directly at scores.sebi.gov.in.")

    # Link to Full Web Dossier / Complaint PDF
    base_url = public_url or os.getenv("PUBLIC_URL") or os.getenv("CLOUDFLARE_URL") or ""
    if base_url and job_id:
        clean_url = base_url.rstrip("/")
        lines.append("")
        lines.append(f"📄 *Full Forensic Dossier & SEBI Complaint:*")
        lines.append(f"{clean_url}/results?job_id={job_id}")

    return "\n".join(lines)

def get_welcome_guide() -> str:
    """Returns the welcoming onboarding message in clean ASCII for Twilio compatibility."""
    return (
        "*Welcome to FinGuard!*\n"
        "_India's Multimodal Financial Deepfake and Scam Shield_\n\n"
        "Forward any suspicious message, audio, video, or link to this chat to analyze it:\n\n"
        "- *Text Forward* - Scans stock tips, Hinglish scam slang and SEBI registration claims.\n"
        "- *Voice Note / Audio* - Checks for AI voice cloning (ElevenLabs, TTS) and speech intent.\n"
        "- *Video* - Detects face deepfakes, AI watermarks, sensor noise and on-screen text.\n"
        "- *Screenshot / Flyer* - OCR scans trading posters and VIP channel invites.\n"
        "- *Link / Website* - Detects typo-squatted fake broker phishing sites.\n"
        "- *APK File* - Detects trojanized fake trading applications.\n\n"
        "Powered by local GPU deepfake models and the official SEBI Registry."
    )

def get_status_guide() -> str:
    """Returns live system status of the FinGuard server."""
    device = get_device()
    now = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    return (
        "⚙️ *FinGuard System Status*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"• *Status:* 🟢 Online & Active\n"
        f"• *Hardware Device:* `{device.upper()}`\n"
        "• *Pipeline Stages:* 9 Multimodal Forensics Stages\n"
        "• *Vision Detector:* ms-eff-gcvit (B0)\n"
        "• *Audio Detector:* Wav2Vec2 GaryStafford\n"
        "• *Transcription:* faster-whisper (float16)\n"
        "• *Reasoning LLM:* Llama 3.1 8B (Ollama)\n"
        "• *SEBI Registry:* Live Static Mirror Active\n"
        f"• *Timestamp:* {now}\n\n"
        "Send or forward any media anytime to scan!"
    )

# ── Specialized Media Analyzers ───────────────────────────────────────────────

def analyze_whatsapp_text(
    text: str,
    job_id: str,
    calculate_verdict_fn,
    build_evidence_fn,
    public_url: Optional[str] = None
) -> str:
    """Analyzes a text forward (URL or financial advisory message)."""
    # 1. Check if the message is primarily a URL
    url_match = re.search(r'https?://[^\s]+', text)
    domain_result = None
    if url_match:
        found_url = url_match.group(0)
        domain_result = scan_domain(found_url)

    # 2. Phishing domain check on text
    stage9 = run_stage9_apk_domain(job_id, ocr_text=text)

    # 3. LLM reasoning on text
    llm = run_stage5_llm(text, job_id)

    # 4. Registry verification
    registry = run_stage6_registry(llm, job_id)

    is_scam = llm.get("is_scam_likely", False)
    if stage9.get("any_threat_detected") or (domain_result and domain_result.get("is_phishing")):
        is_scam = True

    composite_risk = float(llm.get("composite_risk_score", 0.0))
    if domain_result and domain_result.get("is_phishing"):
        composite_risk = max(composite_risk, 0.95)

    fallback_used = llm.get("fallback_used", False)
    degraded_modules = ["stage5_llm"] if fallback_used else []

    verdict = calculate_verdict_fn(
        is_deepfake=False,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_verdict=registry.get("verdict", "not claimed"),
        fallback_used=fallback_used,
        degraded_modules=degraded_modules
    )

    evidence_breakdown = build_evidence_fn(
        is_deepfake=False,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_check=registry,
        sebi_analysis=llm,
        audio_score=0.0,
        vision_score=0.0,
        domain_scan=domain_result or stage9.get("ocr_domain_result"),
        degraded_modules=degraded_modules
    )

    return format_whatsapp_verdict_card(
        verdict=verdict,
        composite_risk=composite_risk,
        scan_type="Text / Stock Tip",
        evidence_breakdown=evidence_breakdown,
        sebi_analysis=llm,
        registry_check=registry,
        domain_scan=domain_result or stage9.get("ocr_domain_result"),
        job_id=job_id,
        public_url=public_url
    )

def analyze_whatsapp_audio(
    audio_path: str,
    job_id: str,
    calculate_verdict_fn,
    build_evidence_fn,
    public_url: Optional[str] = None
) -> str:
    """Analyzes an audio file or voice note."""
    # Stage 4: Transcription
    tx = run_stage4_transcription(audio_path, job_id)
    transcript = tx.get("transcript", "")

    # Stage 3: Audio deepfake & voice cloning
    audio = run_stage3_audio(audio_path, job_id, transcript=transcript)

    # Stage 9: Phishing domain check on transcript
    stage9 = run_stage9_apk_domain(job_id, ocr_text=transcript) if transcript else {}

    # Stage 5: LLM reasoning
    llm = run_stage5_llm(transcript, job_id, segments=tx.get("segments", []))

    # Stage 6: Registry check
    registry = run_stage6_registry(llm, job_id)

    audio_thresh = get_threshold("audio_fake_threshold", 0.5)
    raw_a_score = audio.get("max_score", 0.0)
    audio_score = float(np.clip(raw_a_score, 0.0, 1.0)) if isinstance(raw_a_score, (int, float)) else 0.0

    is_deepfake = audio_score > audio_thresh
    is_scam = llm.get("is_scam_likely", False)
    if stage9.get("any_threat_detected"):
        is_scam = True

    base_risk = float(llm.get("composite_risk_score", 0.0))
    composite_risk = max(base_risk, audio_score if is_deepfake else 0.0)

    fallback_used = llm.get("fallback_used", False)
    degraded_modules = []
    if fallback_used:
        degraded_modules.append("stage5_llm")
    if audio.get("status") == "error":
        degraded_modules.append("stage3_audio")

    verdict = calculate_verdict_fn(
        is_deepfake=is_deepfake,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_verdict=registry.get("verdict", "not claimed"),
        fallback_used=fallback_used,
        degraded_modules=degraded_modules
    )

    evidence_breakdown = build_evidence_fn(
        is_deepfake=is_deepfake,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_check=registry,
        sebi_analysis=llm,
        audio_score=audio_score,
        vision_score=0.0,
        domain_scan=stage9.get("ocr_domain_result"),
        degraded_modules=degraded_modules
    )

    return format_whatsapp_verdict_card(
        verdict=verdict,
        composite_risk=composite_risk,
        scan_type="Voice Note / Audio",
        evidence_breakdown=evidence_breakdown,
        sebi_analysis=llm,
        registry_check=registry,
        audio_score=audio_score,
        domain_scan=stage9.get("ocr_domain_result"),
        job_id=job_id,
        public_url=public_url
    )

def analyze_whatsapp_image(
    image_path: str,
    job_id: str,
    calculate_verdict_fn,
    build_evidence_fn,
    public_url: Optional[str] = None
) -> str:
    """Analyzes an image or screenshot."""
    # Stage 2: Vision deepfake
    vision = run_stage2_vision([image_path], job_id)

    # Stage 7: OCR
    ocr = run_stage7_ocr(image_path, job_id)
    extracted_text = ocr.get("extracted_text", "")

    # Stage 9: Domain check
    stage9 = run_stage9_apk_domain(job_id, ocr_text=extracted_text) if extracted_text else {}

    # Stage 5: LLM
    llm = run_stage5_llm(extracted_text, job_id) if extracted_text and len(extracted_text.strip()) >= 10 else {}

    # Stage 6: Registry
    registry = run_stage6_registry(llm, job_id) if llm else {"verdict": "not claimed", "matched_entity": None}

    vision_thresh = get_vision_threshold()
    raw_v_score = vision.get("max_score", 0.0)
    vision_score = float(np.clip(raw_v_score, 0.0, 1.0)) if isinstance(raw_v_score, (int, float)) else 0.0

    is_deepfake = vision_score > vision_thresh
    is_scam = llm.get("is_scam_likely", False) if llm else False
    if stage9.get("any_threat_detected"):
        is_scam = True

    base_risk = float(llm.get("composite_risk_score", 0.0)) if llm else 0.0
    composite_risk = max(base_risk, vision_score if is_deepfake else 0.0)

    fallback_used = llm.get("fallback_used", False) if llm else False
    degraded_modules = ["stage5_llm"] if fallback_used else []

    verdict = calculate_verdict_fn(
        is_deepfake=is_deepfake,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_verdict=registry.get("verdict", "not claimed"),
        fallback_used=fallback_used,
        degraded_modules=degraded_modules
    )

    evidence_breakdown = build_evidence_fn(
        is_deepfake=is_deepfake,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_check=registry,
        sebi_analysis=llm,
        audio_score=0.0,
        vision_score=vision_score,
        domain_scan=stage9.get("ocr_domain_result"),
        degraded_modules=degraded_modules
    )

    return format_whatsapp_verdict_card(
        verdict=verdict,
        composite_risk=composite_risk,
        scan_type="Screenshot / Image",
        evidence_breakdown=evidence_breakdown,
        sebi_analysis=llm,
        registry_check=registry,
        vision_score=vision_score,
        domain_scan=stage9.get("ocr_domain_result"),
        job_id=job_id,
        public_url=public_url
    )

def analyze_whatsapp_apk(
    apk_path: str,
    job_id: str,
    filename: str = "app.apk",
    public_url: Optional[str] = None
) -> str:
    """Analyzes an Android APK file."""
    result = run_stage9_apk_domain(job_id, apk_path=apk_path)
    apk_r = result.get("apk_result") or {}
    is_suspicious = apk_r.get("is_suspicious", False)
    composite_risk = 1.0 if is_suspicious else 0.0
    verdict = "Warning: Malicious APK Detected" if is_suspicious else "Safe: Official Broker APK"

    return format_whatsapp_verdict_card(
        verdict=verdict,
        composite_risk=composite_risk,
        scan_type="Android APK File",
        apk_result=apk_r,
        job_id=job_id,
        public_url=public_url
    )

def analyze_whatsapp_video(
    video_path: str,
    temp_job_dir: str,
    job_id: str,
    calculate_verdict_fn,
    build_evidence_fn,
    public_url: Optional[str] = None
) -> str:
    """Runs the complete multimodal 9-stage video forensic analysis."""
    # Stage 1: Ingest
    ingest = run_stage1_ingest(video_path, temp_job_dir, job_id)
    ai_watermark = ingest.get("ai_watermark", {})
    has_ai_watermark = bool(ai_watermark.get("watermark_detected"))

    # Stage 2: Vision
    vision = run_stage2_vision(ingest.get("face_frames_paths", []), job_id)

    # Stage 4: Transcription
    tx = run_stage4_transcription(ingest.get("audio_path"), job_id)
    transcript = tx.get("transcript", "")

    # Stage 3: Audio
    audio = run_stage3_audio(
        ingest.get("audio_path"),
        job_id,
        transcript=transcript,
        ai_watermark_detected=has_ai_watermark,
        vision_score=vision.get("max_score", 0.0)
    )

    # Stage 7: Keyframe OCR
    keyframes = ingest.get("keyframes") or ingest.get("face_frames_paths", [])
    video_ocr_result = run_video_keyframes_ocr(keyframes, job_id)
    video_ocr_text = video_ocr_result.get("extracted_text", "").strip()

    # Stage 5: LLM
    combined_text = " ".join(t for t in [transcript, video_ocr_text] if t).strip()
    llm = run_stage5_llm(transcript, job_id, ocr_text=video_ocr_text, segments=tx.get("segments", []))

    # Stage 6: Registry
    registry = run_stage6_registry(llm, job_id)

    # Stage 9: Domain check
    stage9 = run_stage9_apk_domain(job_id, ocr_text=combined_text) if combined_text else {}

    vision_thresh = get_vision_threshold()
    audio_thresh = get_threshold("audio_fake_threshold", 0.5)

    raw_v = vision.get("max_score")
    vision_score = float(np.clip(raw_v, 0.0, 1.0)) if isinstance(raw_v, (int, float)) else 0.0
    raw_a = audio.get("max_score")
    audio_score = float(np.clip(raw_a, 0.0, 1.0)) if isinstance(raw_a, (int, float)) else 0.0

    if has_ai_watermark:
        vision_score = max(vision_score, 0.999)
        is_deepfake = True
    else:
        has_vision_fake = vision_score > vision_thresh
        has_audio_fake = audio_score > audio_thresh
        is_deepfake = bool(has_vision_fake or has_audio_fake)

    is_scam = bool(llm.get("is_scam_likely", False))
    if stage9.get("any_threat_detected"):
        is_scam = True

    base_risk = float(llm.get("composite_risk_score", 0.0))
    media_threat = max(vision_score, audio_score, 1.0 if has_ai_watermark else 0.0)

    if is_deepfake and is_scam:
        composite_risk = max(base_risk, media_threat, 0.95)
    elif is_deepfake:
        composite_risk = max(base_risk, media_threat, 0.90)
    elif is_scam:
        composite_risk = max(base_risk, 0.85)
    else:
        composite_risk = base_risk

    fallback_used = bool(llm.get("fallback_used", False))
    degraded_modules = []
    if fallback_used:
        degraded_modules.append("stage5_llm")
    if audio.get("status") == "error":
        degraded_modules.append("stage3_audio")
    if vision.get("status") == "error":
        degraded_modules.append("stage2_vision")

    verdict = calculate_verdict_fn(
        is_deepfake=is_deepfake,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_verdict=registry.get("verdict", "not claimed"),
        fallback_used=fallback_used,
        degraded_modules=degraded_modules
    )

    evidence_breakdown = build_evidence_fn(
        is_deepfake=is_deepfake,
        is_scam=is_scam,
        composite_risk=composite_risk,
        registry_check=registry,
        sebi_analysis=llm,
        audio_score=audio_score,
        vision_score=vision_score,
        domain_scan=stage9.get("ocr_domain_result"),
        degraded_modules=degraded_modules,
        ai_watermark=ai_watermark
    )

    return format_whatsapp_verdict_card(
        verdict=verdict,
        composite_risk=composite_risk,
        scan_type="Multimodal Video Forensics",
        evidence_breakdown=evidence_breakdown,
        sebi_analysis=llm,
        registry_check=registry,
        vision_score=vision_score,
        audio_score=audio_score,
        ai_watermark=ai_watermark,
        domain_scan=stage9.get("ocr_domain_result"),
        job_id=job_id,
        public_url=public_url
    )
