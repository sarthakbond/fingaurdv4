import pytest
from src.stages.stage8_report import generate_sebi_scores_complaint


def test_clean_asset_produces_clearance_memorandum():
    """Authentic / low-risk assets must produce a Statutory Forensic Clearance Memorandum."""
    clean_data = {
        "job_id": "test-clean-001",
        "verdict": "Low Risk / Compliant",
        "composite_risk_score": 0.05,
        "is_deepfake": False,
        "is_scam": False,
        "target_url_or_asset": "https://zerodha.com",
        "filename": "zerodha.com",
        "scan_type": "url",
        "vision_score": 0.02,
        "audio_score": 0.01,
        "registry_check": {"verdict": "verified"},
    }
    complaint = generate_sebi_scores_complaint(clean_data, "Phishing Domain / URL")
    
    assert "STATUTORY FORENSIC CLEARANCE MEMORANDUM & COMPLIANCE RECORD" in complaint
    assert "SECTION 63, BHARATIYA SAKSHYA ADHINIYAM, 2023" in complaint
    assert "zerodha.com" in complaint
    assert "WITHIN STATUTORY THRESHOLDS" in complaint
    # Must NOT demand criminal FIR on clean asset
    assert "DEMAND FOR POLICE REGISTRATION OF FIRST INFORMATION REPORT" not in complaint


def test_rogue_apk_complaint_matches_apk_evidence():
    """Malicious APK scan must cite package, dangerous SMS permissions, IT Act 43/66/66D & BNS 111."""
    apk_data = {
        "job_id": "test-apk-malware",
        "verdict": "Suspicious APK / Trojan",
        "composite_risk_score": 0.95,
        "scan_type": "apk",
        "filename": "groww_vip_pro.apk",
        "target_url_or_asset": "com.fraud.groww.vip",
        "apk_result": {
            "is_suspicious": True,
            "package_name": "com.fraud.groww.vip",
            "reason": "Impersonates Groww and requests SMS interception permissions.",
            "suspicious_permissions": ["android.permission.RECEIVE_SMS", "android.permission.READ_SMS"],
            "matched_broker": "Groww (Nextbillion Technology Pvt Ltd)",
        },
        "sebi_analysis": {
            "is_scam_likely": True,
            "reasoning": "Fake trading app trojan stealing OTPs."
        }
    }
    complaint = generate_sebi_scores_complaint(apk_data, "Fake Broker APK")

    assert "ROGUE ANDROID TRADING APP / TROJAN MALWARE" in complaint
    assert "groww_vip_pro.apk" in complaint
    assert "com.fraud.groww.vip" in complaint
    assert "android.permission.RECEIVE_SMS" in complaint
    assert "BNS 111" in complaint or "Organized Cyber-Financial Crime" in complaint
    assert "SECTION 63, BHARATIYA SAKSHYA ADHINIYAM, 2023" in complaint


def test_phishing_url_complaint_matches_url_and_spoofed_broker():
    """Phishing URL complaint must cite submitted URL, normalized host, and targeted broker."""
    url_data = {
        "job_id": "test-url-phish",
        "verdict": "Phishing Domain / Unauthorized",
        "composite_risk_score": 0.98,
        "scan_type": "url",
        "target_url_or_asset": "https://secure-zerodha-login.top/login",
        "filename": "https://secure-zerodha-login.top/login",
        "url_result": {
            "is_phishing": True,
            "normalised_host": "secure-zerodha-login.top",
            "legitimate_broker": "Zerodha Broking Ltd",
            "matched_legitimate_domain": "zerodha.com",
            "reason": "Typo-squatting domain mimicking Zerodha login gateway."
        },
        "sebi_analysis": {
            "is_scam_likely": True,
            "reasoning": "Credential harvester."
        }
    }
    complaint = generate_sebi_scores_complaint(url_data, "Phishing Domain / URL")

    assert "PHISHING DOMAIN & BROKER BRAND IMPERSONATION" in complaint
    assert "secure-zerodha-login.top" in complaint
    assert "Zerodha Broking Ltd" in complaint
    assert "Section 69A" in complaint
    assert "SECTION 63, BHARATIYA SAKSHYA ADHINIYAM, 2023" in complaint


def test_audio_voice_clone_complaint_matches_acoustic_findings():
    """Voice deepfake complaint must cite neural backend, peak score, transcript, IT Act 66D & BNS 319(2)."""
    audio_data = {
        "job_id": "test-audio-clone",
        "verdict": "Critical: Deepfake Impersonation",
        "composite_risk_score": 0.92,
        "scan_type": "audio",
        "filename": "cfo_voice_memo.mp3",
        "audio_score": 0.94,
        "audio_backend": "Wav2Vec2 GaryStafford",
        "audio_raw_peak_score": 0.97,
        "audio_windows_flagged": 4,
        "audio_total_windows": 5,
        "transcript": "Transfer ten lakh rupees to account 9876 immediately for the IPO allotment.",
        "is_deepfake": True,
        "is_scam": True,
        "sebi_analysis": {
            "is_scam_likely": True,
            "reasoning": "Voice clone demanding urgent wire transfer."
        }
    }
    complaint = generate_sebi_scores_complaint(audio_data, "Audio Broadcast / Podcast")

    assert "SYNTHETIC VOICE CLONING & BIOMETRIC IMPERSONATION" in complaint
    assert "cfo_voice_memo.mp3" in complaint
    assert "Wav2Vec2" in complaint
    assert "Transfer ten lakh rupees" in complaint
    assert "IT Act Section 66D" in complaint or "Section 66D" in complaint
    assert "BNS 319(2)" in complaint or "Section 319(2)" in complaint


def test_unregistered_claim_complaint_quotes_verbatim_promises():
    """Fraudulent financial claims must cite prohibited return promises and SEBI IA 2013."""
    claim_data = {
        "job_id": "test-claim-fraud",
        "verdict": "High Risk / Prohibited Scheme",
        "composite_risk_score": 0.88,
        "scan_type": "text",
        "filename": "Uploaded Financial Claim / Social Post",
        "transcript": "Guaranteed 50% profit every 24 hours in BankNifty jackpot group. 100% loss proof.",
        "sebi_analysis": {
            "is_scam_likely": True,
            "specific_return_promises": ["Guaranteed 50% profit every 24 hours", "100% loss proof"],
            "claimed_advisor_name": "Jackpot Guru Telegram",
            "reasoning": "Unregistered promises of fixed high-frequency returns."
        },
        "registry_check": {
            "verdict": "not registered",
            "epistemic_status": "UNREGISTERED"
        }
    }
    complaint = generate_sebi_scores_complaint(claim_data, "Text / Social Media Post")

    assert "Jackpot Guru Telegram" in complaint
    assert "Guaranteed 50% profit every 24 hours" in complaint
    assert "SEBI (Investment Advisers) Regulations, 2013" in complaint
    assert "Banning of Unregulated Deposit Schemes Act" in complaint or "BUDS Act" in complaint
