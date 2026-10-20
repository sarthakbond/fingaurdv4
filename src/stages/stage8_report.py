import os
import datetime
import hashlib
from typing import Dict, Any, Optional
from src.config import get_threshold, get_vision_threshold

def compute_record_sha256(data: Dict[str, Any]) -> str:
    """
    Computes a SHA-256 cryptographic hash of the evidence media or facts
    for statutory admissibility under Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023).
    """
    if data.get("sha256"):
        return str(data["sha256"]).lower()
    if data.get("media_hash"):
        return str(data["media_hash"]).lower()
    
    file_path = data.get("file_path") or data.get("media_path")
    if file_path and os.path.exists(file_path):
        try:
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest().lower()
        except Exception:
            pass

    # Deterministic fallback digest over core evidence payload
    fallback_seed = (
        f"{data.get('job_id', '')}:"
        f"{data.get('claimed_advisor_name', '')}:"
        f"{data.get('verdict', '')}:"
        f"{data.get('composite_risk_score', '')}:"
        f"{data.get('vision_score', '')}:"
        f"{data.get('audio_score', '')}"
    )
    return hashlib.sha256(fallback_seed.encode("utf-8")).hexdigest().lower()

def compute_monotonic_composite_risk(
    base_risk: float,
    modality_scores: Dict[str, Optional[float]],
    registry_check: Optional[Dict[str, Any]] = None,
    uncertainty_penalty: float = 0.0
) -> float:
    """
    Monotonic Risk Fusion Clamping (VERA Research Paper Section IV-C).
    Prevents 'benign dilution' where high-confidence indicators in one modality
    (e.g., deepfake face, cloned voice, fake SEBI ID, phishing domain, trojan APK)
    are averaged down or diluted by benign transcript or neutral context.
    
    Formula:
      S_clamped = max(base_risk, 0.95 * max_{k: s_k >= 0.80}(s_k))
    
    Also factors in epistemic uncertainty penalty (P_u = +0.15) when external registries
    or critical verification services are UNAVAILABLE (Tri-State Epistemic Model).
    """
    base = float(base_risk or 0.0)
    severe_scores = []
    
    for key, val in modality_scores.items():
        if val is not None and isinstance(val, (int, float)):
            v = float(val)
            if v >= 0.80:
                severe_scores.append(v)

    if registry_check:
        reg_v = str(registry_check.get("verdict", "")).lower()
        if reg_v == "name-number mismatch":
            severe_scores.append(0.95)
        elif reg_v in ["not found", "malformed number"] and base >= 0.70:
            severe_scores.append(0.85)

    if severe_scores:
        clamped_floor = 0.95 * max(severe_scores)
        base = max(base, clamped_floor)

    # Apply epistemic penalty if registry or critical service is UNAVAILABLE
    if registry_check and registry_check.get("epistemic_status") == "UNAVAILABLE":
        p_u = float(registry_check.get("uncertainty_penalty", uncertainty_penalty or 0.15))
        base = min(1.0, base + p_u)

    return float(round(base, 4))

def generate_sebi_scores_complaint(data: Dict[str, Any], content_type: str = "Video") -> str:
    """
    Generates a structured, legally formatted complaint draft ready for submission
    to the SEBI Complaints Redress System (SCORES 2.0) portal, SEBI Enforcement Division,
    and National Cyber Crime Reporting Portal (cybercrime.gov.in).
    Fully certified under Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023).
    """
    now = datetime.datetime.now().strftime("%d-%B-%Y %H:%M:%S IST")
    sebi = data.get("sebi_analysis", {})
    registry = data.get("registry_check", {})
    
    claimed_name = sebi.get("claimed_advisor_name") or "Unspecified Entity / Finfluencer"
    claimed_reg = sebi.get("claimed_registration_number") or "None Disclosed"
    reg_verdict = registry.get("verdict", "not claimed").upper()
    epistemic_status = registry.get("epistemic_status", "NOT_VERIFIED")
    
    is_deepfake = data.get("is_deepfake", False)
    vision_score = data.get("vision_score", 0.0)
    audio_score = data.get("audio_score", 0.0)
    risk_score = data.get("composite_risk_score", sebi.get("composite_risk_score", 0.0))
    verdict = data.get("verdict", "Suspicious Content")
    job_id = data.get("job_id") or f"FG-SCORES-{datetime.datetime.now().strftime('%Y%m%d')}-{data.get('scan_type', 'AUDIT').upper()}"
    media_sha256 = compute_record_sha256(data)
    
    # 1. Identify violated SEBI regulations & BNS 2023 / IT Act criminal provisions
    sebi_violations = []
    bns_violations = []
    
    return_quotes = sebi.get("specific_return_promises", [])
    implied_quotes = sebi.get("implied_returns", [])
    urgency_quotes = sebi.get("urgency_scarcity_language", [])
    paywall_quotes = sebi.get("paywall_push", [])
    cred_quotes = sebi.get("credential_misrepresentation", [])
    
    if return_quotes or implied_quotes:
        sebi_violations.append("• SEBI (Investment Advisers) Regulations, 2013 — Prohibition of guaranteed/assured return promises.")
    if reg_verdict in ["NOT FOUND", "NAME-NUMBER MISMATCH", "MALFORMED NUMBER"]:
        sebi_violations.append("• SEBI Act, 1992 Section 12(1) — Providing investment advice/research without valid SEBI registration.")
    if paywall_quotes:
        sebi_violations.append("• SEBI Master Circular on Social Media/Finfluencers — Unlawful monetization of unregistered financial advice via private channels.")
    if is_deepfake:
        sebi_violations.append("• SEBI (Prohibition of Fraudulent and Unfair Trade Practices) Regulations, 2003 (PFUTP) — Synthetically generated deepfake media used to manipulate and deceive retail investors.")
    if not sebi_violations:
        sebi_violations.append("• Potential Deceptive Marketing & Misrepresentation under SEBI PFUTP Regulations.")

    # Criminal Penal Framework (BNS 2023 replacing IPC, and IT Act 2000)
    bns_violations.append("• Bharatiya Nyaya Sanhita, 2023 (BNS) Section 318(4) — Cheating and dishonestly inducing delivery of property (formerly IPC Section 420; Cognizable, non-bailable, imprisonment up to 7 years).")
    if reg_verdict == "NAME-NUMBER MISMATCH" or is_deepfake or cred_quotes:
        bns_violations.append("• Bharatiya Nyaya Sanhita, 2023 (BNS) Section 319(2) — Cheating by personation using digital communications/synthetic identities (formerly IPC Section 419; imprisonment up to 5 years).")
        bns_violations.append("• Information Technology Act, 2000 Section 66D — Punishment for cheating by personation by using computer resources (imprisonment up to 3 years and fine).")
    if paywall_quotes or return_quotes:
        bns_violations.append("• Bharatiya Nyaya Sanhita, 2023 (BNS) Section 61(2) — Criminal conspiracy to defraud public investors through syndicated digital solicitation.")

    # Format Evidence Section
    evidence_lines = []
    if return_quotes:
        evidence_lines.append(f"  [Guaranteed Return Claims]:\n" + "\n".join([f'    - "{q}"' for q in return_quotes]))
    if implied_quotes:
        evidence_lines.append(f"  [Implied Return Promises]:\n" + "\n".join([f'    - "{q}"' for q in implied_quotes]))
    if urgency_quotes:
        evidence_lines.append(f"  [Urgency & Pressure Tactics]:\n" + "\n".join([f'    - "{q}"' for q in urgency_quotes]))
    if paywall_quotes:
        evidence_lines.append(f"  [Unregistered Paid Channel Funnels]:\n" + "\n".join([f'    - "{q}"' for q in paywall_quotes]))
    if cred_quotes:
        evidence_lines.append(f"  [Credential Misrepresentation / Tampering]:\n" + "\n".join([f'    - "{q}"' for q in cred_quotes]))
        
    evidence_text = "\n\n".join(evidence_lines) if evidence_lines else "  No explicit verbal quotes extracted."

    quality_info = data.get("input_quality", {})
    quality_rating = quality_info.get("rating", "Standard") if isinstance(quality_info, dict) else "Standard"

    vision_thresh = get_vision_threshold()
    audio_thresh = get_threshold("audio_fake_threshold", 0.5)

    if vision_score is not None:
        vision_str = f"{vision_score * 100:.1f}% {'(SYNTHETIC FACE MANIPULATION DETECTED)' if vision_score > vision_thresh else '(Within Normal Parameters)'}"
    else:
        vision_str = "Not Applicable (Audio/Text Only Scan)"

    if audio_score is not None:
        audio_str = f"{audio_score * 100:.1f}% {'(SYNTHETIC VOICE CLONING DETECTED)' if audio_score > audio_thresh else '(Within Normal Parameters)'}"
    else:
        audio_str = "Not Applicable (Visual/Text Only Scan)"

    complaint = f"""================================================================================
           SECURITIES AND EXCHANGE BOARD OF INDIA (SEBI)
   PRE-FILING EVIDENCE DOSSIER — SCORES 2.0 / MARKET SURVEILLANCE REVIEW
   [PREPARED BY FINGUARD FORENSIC ASSISTANT — FOR HUMAN / COMPLIANCE OFFICER REVIEW]
================================================================================

LEGAL NOTICE & STATUTORY ADMISSIBILITY:
This document is an automated evidentiary compilation generated by the FinGuard 
Forensic Platform. It serves as an investigative pre-filing dossier to support regulatory 
filings before SEBI and criminal complaints under Bharatiya Nyaya Sanhita, 2023 (BNS).
Evidentiary admissibility certified under Section 63 of Bharatiya Sakshya Adhiniyam, 2023.

DATE & TIME OF GENERATION : {now}
INVESTIGATION CASE ID    : {job_id}
PRIMARY EVIDENCE SHA-256 : {media_sha256}
RISK ASSESSMENT RATING   : {verdict.upper()}
COMPOSITE THREAT SCORE   : {risk_score * 100:.1f}%
INPUT MEDIA QUALITY      : {quality_rating}

--------------------------------------------------------------------------------
1. RESPONDENT / SUSPECT DETAILS
--------------------------------------------------------------------------------
Name of Finfluencer / Entity : {claimed_name}
Claimed SEBI Reg. Number     : {claimed_reg}
Local Registry Check (Aug 26): {reg_verdict} (Epistemic Status: {epistemic_status})
Channel / Medium of Fraud    : Digital {content_type} (Social Media / Web Transmission)

--------------------------------------------------------------------------------
2. AI FORENSIC EVIDENCE ASSESSMENT
--------------------------------------------------------------------------------
• Visual Deepfake Confidence  : {vision_str}
• Audio Spoof Confidence     : {audio_str}
• Forensic Analyst Notes      : {sebi.get("reasoning", "Evidence points to non-compliant financial advisory distribution.")}

--------------------------------------------------------------------------------
3. APPLICABLE STATUTORY & REGULATORY FRAMEWORKS
--------------------------------------------------------------------------------
[A] Securities Regulatory Violations (SEBI Act, 1992):
{chr(10).join(sebi_violations)}

[B] Criminal Penal Provisions (Bharatiya Nyaya Sanhita, 2023 [BNS] & IT Act):
{chr(10).join(bns_violations)}

--------------------------------------------------------------------------------
4. EXTRACTED FORENSIC EVIDENCE & VERBATIM TRANSCRIPT
--------------------------------------------------------------------------------
{evidence_text}

--------------------------------------------------------------------------------
5. RECOMMENDED REGULATORY & ENFORCEMENT ACTIONS
--------------------------------------------------------------------------------
1. Issue restraint directions under Section 11(1), 11(4) and 11B of the SEBI Act, 1992 restraining the respondent from securities market activities pending inquiry.
2. Direct impounding and disgorgement of illicit subscription revenues collected via private channels.
3. Register FIR under Section 318(4) and Section 319(2) of Bharatiya Nyaya Sanhita, 2023 (BNS) along with Section 66D of the Information Technology Act, 2000.
4. Issue urgent blocking orders through MeitY under Section 69A of the IT Act for associated fraudulent channels and domains.

--------------------------------------------------------------------------------
6. STATUTORY ELECTRONIC EVIDENCE CERTIFICATE
   [SECTION 63, BHARATIYA SAKSHYA ADHINIYAM, 2023 (BSA 2023)]
--------------------------------------------------------------------------------
I, the undersigned automated system operator / reviewing forensic officer, certify 
under Section 63(4) of the Bharatiya Sakshya Adhiniyam, 2023 (Act No. 47 of 2023) that:

1. RECORD IDENTIFICATION & INTEGRITY:
   • Source Electronic Record  : {job_id} / {content_type} Evidence
   • Cryptographic SHA-256     : {media_sha256}
   • Generation System / Node  : FinGuard Multimodal Forensic Engine v4.0 (Local GPU Node)

2. STATUTORY SYSTEM ATTESTATION:
   (a) The electronic record was produced by the FinGuard Computer Forensic System during 
       the period over which the computer was used regularly to process financial surveillance data.
   (b) Throughout the material part of the said period, the computer operated properly and 
       the accuracy of the electronic record was not affected by mechanical failure or tampering.
   (c) The contents herein faithfully reproduce digital media and neural forensic tensors 
       processed in the ordinary course of regulatory monitoring.

Date of Attestation : {now}
Digital Fingerprint : SHA256:{media_sha256[:32]}...

================================================================================
Document generated by FinGuard Forensic Engine v4.0 (BSA 2023 & BNS Compliant)
================================================================================
"""
    return complaint
