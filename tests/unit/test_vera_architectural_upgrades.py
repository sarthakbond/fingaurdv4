"""
Unit tests for VERA-inspired architectural upgrades in FinGuard:
1. Monotonic Risk Fusion Clamping (VERA Section IV-C) - Prevents benign dilution attacks.
2. Statutory Admissibility under Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023)
   and criminal penal citations under Bharatiya Nyaya Sanhita, 2023 (BNS 2023 Sections 318(4) & 319(2)).
3. Tri-State Epistemic Verification Model (VERIFIED, NOT_VERIFIED, UNAVAILABLE) with failsafe penalty (+0.15).
"""

import pytest
from src.stages.stage8_report import (
    compute_monotonic_composite_risk,
    generate_sebi_scores_complaint,
    compute_record_sha256,
)
from src.pdf_generator import generate_complaint_pdf
from app import calculate_calibrated_verdict

def test_monotonic_risk_fusion_clamping():
    """
    Verify that when an indicator has high confidence (>= 0.80),
    the composite risk is clamped to at least 0.95 * max(s_k),
    preventing benign transcript from diluting a high-risk deepfake or scam flag.
    """
    # Case 1: Scammer appends benign disclaimer, LLM base risk is low (0.15)
    # But visual deepfake score is 0.92
    base_risk = 0.15
    modality_scores = {
        "vision_score": 0.92,
        "audio_score": 0.10,
        "ai_watermark": 0.0,
    }
    clamped_risk = compute_monotonic_composite_risk(base_risk, modality_scores)
    # Floor must be at least 0.95 * 0.92 = 0.874
    assert clamped_risk >= 0.874
    assert clamped_risk >= base_risk

def test_monotonic_risk_fusion_clean_content():
    """
    Verify that benign educational content without any severe anomaly
    is NOT falsely elevated by clamping.
    """
    base_risk = 0.05
    modality_scores = {
        "vision_score": 0.12,
        "audio_score": 0.08,
        "ai_watermark": 0.0,
    }
    clamped_risk = compute_monotonic_composite_risk(base_risk, modality_scores)
    assert clamped_risk == 0.05

def test_tri_state_epistemic_uncertainty_penalty():
    """
    Verify that when the registry verification service is UNAVAILABLE,
    a zero-trust epistemic penalty (+0.15) is added to the score.
    """
    base_risk = 0.20
    modality_scores = {"vision_score": 0.0, "audio_score": 0.0}
    registry_check = {
        "verdict": "unavailable",
        "epistemic_status": "UNAVAILABLE",
        "uncertainty_penalty": 0.15
    }
    clamped_risk = compute_monotonic_composite_risk(
        base_risk, modality_scores, registry_check=registry_check
    )
    # 0.20 + 0.15 = 0.35
    assert clamped_risk == 0.35

    # Also verify calculate_calibrated_verdict routes unavailable registry to Suspicious
    verdict = calculate_calibrated_verdict(
        is_deepfake=False,
        is_scam=False,
        composite_risk=clamped_risk,
        registry_verdict="unavailable"
    )
    assert verdict == "Suspicious: Review Recommended"

def test_sebi_scores_complaint_bsa_2023_statutory_certificate():
    """
    Verify that the generated SCORES complaint dossier contains:
    - Section 63 Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023) Electronic Evidence Certificate.
    - Bharatiya Nyaya Sanhita, 2023 (BNS) Section 318(4) & 319(2) citations.
    - Cryptographic SHA-256 evidence digest.
    """
    dummy_data = {
        "job_id": "FG-TEST-BSA2023",
        "verdict": "Critical: Deepfake + Scam",
        "composite_risk_score": 0.95,
        "is_deepfake": True,
        "vision_score": 0.94,
        "audio_score": 0.88,
        "sebi_analysis": {
            "claimed_advisor_name": "Rakesh Jhunjhunwala AI Clone",
            "claimed_registration_number": "INA000000000",
            "specific_return_promises": ["Double your money in 3 days"],
            "paywall_push": ["Join private VIP WhatsApp channel"],
            "credential_misrepresentation": ["Authorized SEBI VIP Wealth Desk"],
            "reasoning": "High-confidence deepfake face synthesis combined with guaranteed return promises."
        },
        "registry_check": {
            "verdict": "name-number mismatch",
            "epistemic_status": "NOT_VERIFIED",
            "explanation": "Registration belongs to genuine institutional broker, not claimant."
        }
    }

    report_text = generate_sebi_scores_complaint(dummy_data, content_type="Video")

    # Assert BSA 2023 Section 63 certificate presence
    assert "SECTION 63, BHARATIYA SAKSHYA ADHINIYAM, 2023" in report_text
    assert "BSA 2023" in report_text
    assert "Section 63(4)" in report_text
    assert "PRIMARY EVIDENCE SHA-256" in report_text

    # Assert BNS 2023 criminal sections
    assert "Bharatiya Nyaya Sanhita, 2023" in report_text or "BNS" in report_text
    assert "Section 318(4)" in report_text
    assert "Section 319(2)" in report_text
    assert "Section 316(2)" in report_text or "BNS Section 316" in report_text
    assert "Section 66D" in report_text

    # Assert Special Economic & Cyber Statutes
    assert "Banning of Unregulated Deposit Schemes Act" in report_text or "BUDS Act" in report_text
    assert "Consumer Protection Act, 2019" in report_text
    assert "Information Technology Rules, 2021" in report_text or "IT Rules" in report_text

def test_included_laws_catalog_structure():
    """Verify that the master statutory catalog exposes all 6 core legal domains."""
    from src.stages.stage8_report import get_all_included_laws
    catalog = get_all_included_laws()
    assert "securities_regulations" in catalog
    assert "criminal_penal_code" in catalog
    assert "cyber_law" in catalog
    assert "economic_banking_deposits" in catalog
    assert "consumer_protection" in catalog
    assert "evidentiary_certification" in catalog
    assert len(catalog["securities_regulations"]["statutes"]) >= 5
    assert len(catalog["criminal_penal_code"]["statutes"]) >= 6

def test_pdf_generation_with_bsa_2023_certificate():
    """
    Verify that generate_complaint_pdf successfully compiles the BSA 2023
    Section 63 certified complaint into a valid PDF binary.
    """
    dummy_data = {
        "job_id": "FG-TEST-PDF-BSA",
        "verdict": "Critical: Deepfake + Scam",
        "composite_risk_score": 0.95,
        "is_deepfake": True,
        "vision_score": 0.92,
        "audio_score": 0.85,
        "sebi_analysis": {
            "claimed_advisor_name": "Deepfake Impersonator",
            "claimed_registration_number": "INA000001234",
            "specific_return_promises": ["100% daily returns guaranteed"],
            "reasoning": "Deepfake video with fake SEBI ID."
        },
        "registry_check": {
            "verdict": "not found",
            "epistemic_status": "NOT_VERIFIED"
        }
    }
    complaint_text = generate_sebi_scores_complaint(dummy_data, content_type="Video")
    pdf_bytes = generate_complaint_pdf(complaint_text, metadata={"job_id": "FG-TEST-PDF-BSA"})

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF Magic header
    assert pdf_bytes.startswith(b"%PDF")
