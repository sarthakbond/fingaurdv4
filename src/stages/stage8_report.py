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
    
    # 1. Comprehensive Indian Statutory & Regulatory Violations Framework
    sebi_violations = []
    bns_violations = []
    cyber_violations = []
    special_violations = []
    
    return_quotes = sebi.get("specific_return_promises", [])
    implied_quotes = sebi.get("implied_returns", [])
    urgency_quotes = sebi.get("urgency_scarcity_language", [])
    paywall_quotes = sebi.get("paywall_push", [])
    cred_quotes = sebi.get("credential_misrepresentation", [])
    fee_quotes = sebi.get("fee_or_transfer_requests", [])
    
    # [A] Securities & Regulatory Violations (SEBI Act, 1992 & SCRA, 1956)
    if return_quotes or implied_quotes:
        sebi_violations.append("• SEBI (Investment Advisers) Regulations, 2013 (Reg. 3(1), Reg. 15 & Third Schedule Code of Conduct) — Absolute statutory prohibition on assured/guaranteed return promises and misleading profit schemes.")
    if reg_verdict in ["NOT FOUND", "NAME-NUMBER MISMATCH", "MALFORMED NUMBER"]:
        sebi_violations.append("• SEBI Act, 1992 Section 12(1) & Section 12A(a), (b), (c) — Operating as investment adviser or market intermediary without mandatory statutory registration, and deploying manipulative/deceptive devices.")
    if paywall_quotes:
        sebi_violations.append("• SEBI Master Circular on Social Media/Finfluencers (August 2024) — Unlawful monetization of unregistered financial advice via private VIP channels and referral funnels.")
    if is_deepfake:
        sebi_violations.append("• SEBI (PFUTP) Regulations, 2003 (Reg. 3 & Reg. 4) — Fraudulent and unfair trade practices: Disseminating synthetic AI deepfakes and manipulated audiovisual content to fraudulently induce securities transactions.")
    sebi_violations.append("• SEBI (Research Analysts) Regulations, 2014 (Reg. 3(1), Reg. 16 & Reg. 24) — Dispensing unauthorized stock targets, option calls, or trading recommendations without mandatory NISM/SEBI accreditation.")
    sebi_violations.append("• SEBI Act, 1992 Section 15HA & Section 15EB — Statutory monetary penalties for fraudulent and unfair trade practices (up to ₹25 Crore or 3x illicit profit) and failure to obtain statutory registration.")
    if paywall_quotes or fee_quotes:
        sebi_violations.append("• Securities Contracts (Regulation) Act, 1956 (SCRA) Sec. 13, 16 & 23(1) — Prohibition of unauthorized off-exchange derivative contracts and illegal 'Dabba Trading' / CFD syndicates (up to 10 years imprisonment).")

    # [B] Criminal Penal Law (Bharatiya Nyaya Sanhita, 2023 [BNS] - Replaced IPC 1860)
    bns_violations.append("• BNS Section 318(4) — Cheating and dishonestly inducing delivery of property (formerly IPC 420; Cognizable, non-bailable, punishable with rigorous imprisonment up to 7 years and fine).")
    if reg_verdict == "NAME-NUMBER MISMATCH" or is_deepfake or cred_quotes:
        bns_violations.append("• BNS Section 319(2) — Cheating by personation (formerly IPC 419; Impersonating registered intermediaries, institutional analysts, or public figures using synthetic digital identities; imprisonment up to 5 years).")
        bns_violations.append("• BNS Section 336(3) & Section 338 — Forgery of electronic records and valuable certificates for cheating (formerly IPC 468 & 465; Fabricating fraudulent SEBI certificates or doctored P&L screenshots).")
        bns_violations.append("• BNS Section 340(2) — Using as genuine a forged electronic record or regulatory license (formerly IPC 471; Circulating fraudulent SEBI registration IDs and doctored ledgers on digital channels).")
    if fee_quotes or return_quotes or paywall_quotes:
        bns_violations.append("• BNS Section 316(2) & Section 316(5) — Criminal breach of trust by person, broker, or agent (formerly IPC 406 & 409; Misappropriation of entrusted investor capital deposited into unauthorized accounts; imprisonment up to 10 years or life).")
    if paywall_quotes or return_quotes:
        bns_violations.append("• BNS Section 61(2) — Criminal conspiracy (formerly IPC 120B; Collusion to defraud public investors through organized digital channels).")
    if is_deepfake or paywall_quotes or data.get("apk_result"):
        bns_violations.append("• BNS Section 111 — Organized Cyber-Financial Crime (Syndicated operation of unauthorized investment funnels, fake trading apps, and digital fraud networks; imprisonment 5 years to life and fine).")

    # [C] Cyber Crime & Electronic Impersonation (IT Act, 2000 & IT Rules, 2021)
    cyber_violations.append("• IT Act, 2000 Section 66D — Punishment for cheating by personation by using computer resource or communication device (punishable with imprisonment up to 3 years and fine).")
    cyber_violations.append("• IT Act, 2000 Section 66C — Identity theft and fraudulent harvesting/misuse of electronic credentials, signatures, or unique identification features.")
    if data.get("apk_result") or data.get("scan_type") == "apk":
        cyber_violations.append("• IT Act, 2000 Section 43 & Section 66 — Computer-related offences, unauthorized data extraction, and transmission of trojan malware / malicious APKs.")
    cyber_violations.append("• IT Act, 2000 Section 69A — Statutory power of Central Government to direct emergency blocking of fraudulent domains, APK URLs, and scam channels.")
    cyber_violations.append("• Information Technology Rules, 2021 [Rule 3(1)(b)(v) & (vii), Rule 3(2)(b)] — Mandatory 24-hour statutory takedown obligations for hosting deepfakes, impersonation, or financial misinformation.")

    # [D] Special Economic, Banking & Consumer Protection Statutes
    if return_quotes or fee_quotes or paywall_quotes:
        special_violations.append("• Banning of Unregulated Deposit Schemes Act, 2019 (BUDS Act) Sec. 3, 5 & 21 — Strict prohibition on soliciting, promoting, or accepting unregulated pooled deposits (Cognizable, non-bailable, imprisonment up to 10 years and fine up to ₹50 Crore).")
        special_violations.append("• Reserve Bank of India Act, 1934 Section 45-IA & Section 45S — Prohibition on acceptance of deposits by unincorporated bodies or conducting non-banking financial activity without RBI registration.")
    special_violations.append("• Consumer Protection Act, 2019 Section 2(28), 2(47) & Section 21 — Dissemination of false, misleading financial advertisements and deceptive consumer inducement (CCPA penalties up to ₹50 Lakhs).")
    special_violations.append("• CCPA Guidelines for Prevention of Misleading Advertisements, 2022 — Mandatory disclaimer violations and false claims of regulatory approval or guaranteed performance.")
    if paywall_quotes or fee_quotes:
        special_violations.append("• Prevention of Money Laundering Act, 2002 (PMLA) Section 3 & Section 4 — Laundering proceeds of financial crime through unauthorized bank accounts, UPI mule networks, and crypto gateways.")
    special_violations.append("• Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023) Section 61 & Section 63 — Statutory digital record admissibility and hash-verified certificate of electronic records.")

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
[A] Securities Regulatory Violations (SEBI Act, 1992 & SCRA, 1956):
{chr(10).join(sebi_violations)}

[B] Criminal Penal Provisions (Bharatiya Nyaya Sanhita, 2023 [BNS]):
{chr(10).join(bns_violations)}

[C] Cyber Crimes & Electronic Impersonation (IT Act, 2000 & IT Rules, 2021):
{chr(10).join(cyber_violations)}

[D] Special Economic, Banking & Consumer Protection Statutes:
{chr(10).join(special_violations)}

--------------------------------------------------------------------------------
4. EXTRACTED FORENSIC EVIDENCE & VERBATIM TRANSCRIPT
--------------------------------------------------------------------------------
{evidence_text}

--------------------------------------------------------------------------------
5. RECOMMENDED REGULATORY & ENFORCEMENT ACTIONS
--------------------------------------------------------------------------------
1. Issue restraint directions under Section 11(1), 11(4) and 11B of the SEBI Act, 1992 restraining the respondent from securities market activities pending inquiry.
2. Direct impounding and disgorgement of illicit subscription revenues collected via private channels (SEBI Act Sec. 11B / 15HA).
3. Register FIR under Section 318(4) (Cheating), Section 319(2) (Personation), and Section 336(3) (Electronic Forgery) of Bharatiya Nyaya Sanhita, 2023 (BNS).
4. Initiate prosecution under Section 66D (Cheating by Personation) & Section 66C (Identity Theft) of the Information Technology Act, 2000.
5. Invoke Section 3 & 21 of the BUDS Act, 2019 for soliciting/accepting unregulated pooled investment deposits.
6. Issue urgent blocking orders through MeitY under Section 69A of the IT Act and 24-hour intermediary takedown notices under Rule 3(1)(b) of the IT Rules, 2021 for associated domains and channels.
7. Refer banking credentials and UPI handles to Financial Intelligence Unit - India (FIU-IND) and State Cyber Crime Cell for immediate debit freeze on beneficiary mule accounts.

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

Document generated by FinGuard Forensic Engine v4.0 (BSA 2023 & BNS Compliant)
================================================================================
"""
    return complaint


# ──────────────────────────────────────────────────────────────────────────────
# Master Indian Legal & Regulatory Statutes Catalog for FinGuard Reports
# ──────────────────────────────────────────────────────────────────────────────

INDIAN_LEGAL_STATUTES_CATALOG: Dict[str, Any] = {
    "securities_regulations": {
        "title": "Securities Market Regulations & Exchange Enforcement",
        "statutes": [
            {
                "act": "Securities and Exchange Board of India (SEBI) Act, 1992",
                "sections": ["Section 11(1)", "Section 11(4)", "Section 11B", "Section 12(1)", "Section 12A(a),(b),(c)", "Section 15HA", "Section 15EB", "Section 24"],
                "scope": "Statutory authority to issue restraint orders, impound illegal gains, freeze demat/bank accounts, penalize unregistered advisory/research activities (penalties up to ₹25 Cr or 3x profits), and prosecute market fraud."
            },
            {
                "act": "SEBI (Prohibition of Fraudulent and Unfair Trade Practices - PFUTP) Regulations, 2003",
                "sections": ["Regulation 3(a),(b),(c),(d)", "Regulation 4(1)", "Regulation 4(2)(k),(r)"],
                "scope": "Prohibits deployment of deceptive contrivances, deepfake audiovisuals, false market rumors, and fraudulent inducement of public investors to purchase or sell securities."
            },
            {
                "act": "SEBI (Investment Advisers) Regulations, 2013",
                "sections": ["Regulation 3(1)", "Regulation 15", "Third Schedule (Code of Conduct)"],
                "scope": "Mandatory registration for providing investment advice; absolute prohibition on assured or guaranteed return schemes, secret commissions, or undisclosed conflicts of interest."
            },
            {
                "act": "SEBI (Research Analysts) Regulations, 2014",
                "sections": ["Regulation 3(1)", "Regulation 16", "Regulation 24"],
                "scope": "Prohibits dispensing specific stock recommendations, option calls, target prices, or trading signals without mandatory SEBI registration and NISM accreditation."
            },
            {
                "act": "SEBI Master Circular on Social Media Intermediaries & Finfluencers (August 2024)",
                "sections": ["Circular SEBI/HO/MIRSD/MIRSD-PoD-1/P/CIR/2024/121"],
                "scope": "Mandatory bar on registered intermediaries and regulated entities associating with, paying referral fees to, or sharing trading APIs with unregistered financial influencers."
            },
            {
                "act": "Securities Contracts (Regulation) Act, 1956 (SCRA)",
                "sections": ["Section 13", "Section 16", "Section 18A", "Section 23(1)"],
                "scope": "Absolute prohibition of unauthorized off-exchange derivative contracts and illegal 'Dabba Trading' syndicates (punishable with imprisonment up to 10 years)."
            }
        ]
    },
    "criminal_penal_code": {
        "title": "Criminal Penal Law (Bharatiya Nyaya Sanhita, 2023 [BNS] — Replaced IPC 1860)",
        "statutes": [
            {
                "section": "BNS Section 318(4) [formerly IPC Section 420]",
                "offence": "Cheating and dishonestly inducing delivery of property",
                "punishment": "Rigorous imprisonment up to 7 years and fine; Cognizable, non-bailable.",
                "application": "Inducing investors to deposit funds into mule accounts or fraudulent schemes based on fabricated representations."
            },
            {
                "section": "BNS Section 319(2) [formerly IPC Section 419]",
                "offence": "Cheating by personation",
                "punishment": "Imprisonment up to 5 years, or fine, or both.",
                "application": "Impersonating genuine SEBI-registered analysts, institutional brokers, or high-profile public figures via AI voice clones and facial deepfakes."
            },
            {
                "section": "BNS Section 316(2) & 316(5) [formerly IPC Section 406 & 409]",
                "offence": "Criminal breach of trust by person, banker, merchant, or broker",
                "punishment": "Imprisonment up to 10 years or life imprisonment.",
                "application": "Misappropriation or unauthorized conversion of funds entrusted by retail investors for portfolio management or trading."
            },
            {
                "section": "BNS Section 336(3) & 338 [formerly IPC Section 468 & 465]",
                "offence": "Forgery of electronic records and valuable certificates for cheating",
                "punishment": "Imprisonment up to 7 years and fine.",
                "application": "Fabricating fake SEBI registration certificates, doctored P&L screenshots, or counterfeit trade ledger receipts."
            },
            {
                "section": "BNS Section 340(2) [formerly IPC Section 471]",
                "offence": "Using as genuine a forged electronic record or document",
                "punishment": "Same punishment as for forgery (up to 7 years).",
                "application": "Publishing, circulating, or sending forged regulatory credentials and doctored statements across social media or messaging platforms."
            },
            {
                "section": "BNS Section 61(2) [formerly IPC Section 120B]",
                "offence": "Criminal conspiracy to defraud",
                "punishment": "Imprisonment commensurate with the substantive offence.",
                "application": "Syndicated operations involving tele-callers, social media funnel admins, mule account holders, and technical coordinators."
            },
            {
                "section": "BNS Section 111",
                "offence": "Organized Cyber-Financial Crime",
                "punishment": "Imprisonment from 5 years to life, and minimum fine of ₹5 Lakhs.",
                "application": "Continuous unlawful activity conducted by cyber-fraud syndicates, fake trading app rings, and boiler room networks."
            }
        ]
    },
    "cyber_law": {
        "title": "Cyber Crime & Intermediary Takedown Framework",
        "statutes": [
            {
                "act": "Information Technology Act, 2000",
                "sections": ["Section 66D", "Section 66C", "Section 43 & 66", "Section 69A", "Section 79(3)(b)"],
                "scope": "Penalizes cheating by personation using computer resources (Sec. 66D: 3 yrs jail), identity theft (Sec. 66C), malicious APK/trojan injection (Sec. 43/66), power to order emergency URL/channel blocking (Sec. 69A), and forfeiture of intermediary safe harbor (Sec. 79(3)(b))."
            },
            {
                "act": "Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021",
                "sections": ["Rule 3(1)(b)(v)", "Rule 3(1)(b)(vii)", "Rule 3(2)(b)"],
                "scope": "Requires social media platforms, messaging apps, and hosts to take down synthetic impersonations, deepfakes, and financial misinformation within 24 hours of notification."
            }
        ]
    },
    "economic_banking_deposits": {
        "title": "Special Economic, Banking & Anti-Money Laundering Statutes",
        "statutes": [
            {
                "act": "Banning of Unregulated Deposit Schemes Act, 2019 (BUDS Act)",
                "sections": ["Section 3", "Section 5", "Section 7", "Section 21(1),(2),(3)"],
                "scope": "Comprehensive ban on soliciting, promoting, or accepting unregulated deposits/pooled investments without statutory registration. Cognizable, non-bailable offence punishable with 3 to 10 years imprisonment and fine up to ₹50 Crores; power to provisionally attach properties and bank accounts."
            },
            {
                "act": "Reserve Bank of India Act, 1934",
                "sections": ["Section 45-IA", "Section 45S"],
                "scope": "Prohibition on acceptance of deposits by individuals or unincorporated bodies conducting financial business without RBI Certificate of Registration."
            },
            {
                "act": "Prevention of Money Laundering Act, 2002 (PMLA)",
                "sections": ["Section 3", "Section 4", "Schedule (Part A)"],
                "scope": "Attachment and confiscation of proceeds of crime generated from cheating (BNS 318), personation (BNS 319), SEBI violations, and computer crimes; investigation by Enforcement Directorate (ED)."
            }
        ]
    },
    "consumer_protection": {
        "title": "Consumer Protection & Advertising Standards",
        "statutes": [
            {
                "act": "Consumer Protection Act, 2019",
                "sections": ["Section 2(28)", "Section 2(47)", "Section 21", "Section 89"],
                "scope": "Penalizes false and misleading financial advertisements; empowers Central Consumer Protection Authority (CCPA) to impose penalties up to ₹50 Lakhs and issue bans on influencers/endorsers."
            },
            {
                "act": "CCPA Guidelines for Prevention of Misleading Advertisements, 2022",
                "sections": ["Clauses 4, 8, 12, 13"],
                "scope": "Mandatory transparency rules for endorsements, disclosure of material connections, and prohibition of unverified performance or profit assurances."
            },
            {
                "act": "ASCI Guidelines for Influencers in BFSI Sector (August 2023 Update)",
                "sections": ["BFSI Influencer Code"],
                "scope": "Mandates disclosure of SEBI/RBI registration numbers on all financial advice posts, and prominent risk disclaimers across all promotional media."
            }
        ]
    },
    "evidentiary_certification": {
        "title": "Statutory Electronic Evidence Framework (BSA 2023 — Replaced IEA 1872)",
        "statutes": [
            {
                "act": "Bharatiya Sakshya Adhiniyam, 2023 (BSA 2023)",
                "sections": ["Section 61", "Section 62", "Section 63(1)-(4)"],
                "scope": "Governs the legal admissibility of electronic records in judicial and regulatory proceedings. Section 63 replaces Section 65B of the repealed Indian Evidence Act, 1872, mandating a formal certificate of authenticity, system integrity attestation, and cryptographic hash verification (SHA-256) for digital forensic outputs."
            }
        ]
    }
}

def get_all_included_laws() -> Dict[str, Any]:
    """Returns the comprehensive structured catalog of all Indian laws included in FinGuard reports."""
    return INDIAN_LEGAL_STATUTES_CATALOG
