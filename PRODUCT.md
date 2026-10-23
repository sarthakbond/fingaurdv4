# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **B2B Stockbroker Compliance & Marketing Teams** (Zerodha, Groww, Angel One, Upstox): Regulatory risk officers verifying influencer marketing collateral, social video endorsements, and affiliate pipelines before fee disbursement to avoid SEBI August 2024 circular liabilities.
- **Retail Investors & Traders**: Everyday Indian retail market participants encountering viral finfluencer claims, WhatsApp/Telegram investment group tips, questionable broker download APKs, and typosquatted login links.

## Product Purpose
FinGuard is an air-gapped, local-first multi-modal forensic gateway and regulatory intelligence engine engineered for the Indian financial ecosystem. It enables instant verification of media (deepfake video/audio detection), regulatory compliance (SEBI research analyst/investment adviser registration cross-checking), app authenticity (rogue APK inspection), and domain safety (phishing detection), while automatically preparing structured SEBI SCORES 2.0 complaint dossiers under DPDP Act 2023 privacy controls.

## Positioning
Unlike generic deepfake detectors or cloud-dependent compliance tools, FinGuard is built specifically for Indian financial regulations (SEBI IA 2013, RA 2014, PFUTP 2003, and the August 2024 SEBI Finfluencer Circular). It runs locally within a constrained 6GB VRAM hardware envelope (RTX 4050) with automated PII scrubbing (Aadhaar, PAN, UPI, bank accounts) guaranteeing zero cloud retention under the DPDP Act 2023.

## Operating Context
- Web dashboard accessed via browser (local FastAPI backend at `localhost:8000` or Cloudflare tunnel) for deep multi-modal forensic inspection, timeline scrubbing, and complaint drafting.
- Chrome Extension (Manifest V3) running as an ambient browser sentinel with context-menu inspection, active URL verification, and in-page alert toasts for social video and trading websites.
- High-throughput affiliate pipeline audits where compliance teams process creator video submissions before affiliate commission clearance.

## Capabilities and Constraints
- **9-Stage Multi-Modal Pipeline**:
  1. Ephemeral sandboxing & scene-cut aware adaptive sampling with Google Gemini/Veo watermark detection.
  2. Dual-stream visual deepfake detection: spatial pixel domain (EfficientNet-B4) + frequency noise domain (Xception SRM).
  3. Acoustic voice clone & spoof classifier via Wav2Vec2.
  4. Multilingual speech transcription (Hindi/English code-mixed) via faster-whisper.
  5. DPDP Act 2023 Privacy-Enhancing Technology (PET) engine: local regex redaction of Indian PII before LLM analysis.
  6. Regulatory reasoning: local Ollama LLaMA 3.1 auditing 6 SEBI risk factors with sub-millisecond deterministic regex fallback.
  7. SEBI registration fuzzy cross-check against official registry database (RapidFuzz).
  8. Static security inspection: Rogue APK manifest decompilation (Androguard) and typosquatted domain phishing detection (Levenshtein distance).
  9. Automated SCORES 2.0 formal legal complaint generator.
- **Hardware Budget**: Sequential model execution tailored for a 6GB VRAM budget with strict memory deallocation (`torch.cuda.empty_cache()`).
- **Data Privacy**: Local-first, ephemeral processing with zero persistent retention of unredacted user media.

## Brand Commitments
- **Name**: FinGuard (FraudShield-SEBI Pro v4.0).
- **Tone & Aesthetic**: Minimalist, human, and authentic. Distinctly avoided from cliché AI-generated dark-mode neon/synthwave or template frontends. Light-colored, crisp, high-clarity institutional interface designed for high-stakes financial and legal review without sacrificing or hiding any operational features.
- **Tone of Voice**: Authoritative, objective, forensic, and protective. Clear risk scoring (Low, Moderate, High, Severe) with direct statutory citations.

## Evidence on Hand
- `dataset/`: Ground truth SEBI intermediary registries, sample test videos, audio clips, and reference data.
- `extension/`: Working Manifest V3 Chrome Extension (`background.js`, `content.js`, `popup.html`, `popup.css`, `popup.js`).
- `static/`: Frontend web interface (`index.html`, `css/`, `js/`).
- `tests/`: Automated test suite for backend pipeline stages.

## Product Principles
1. **Uncompromising Forensic Rigor**: Never output an unsubstantiated risk score; every flag must link to concrete visual/acoustic anomaly signals or codified SEBI regulations.
2. **Local-First Privacy by Default**: Zero PII leakage. Protect user and whistleblower privacy with local redacting before any model ingestion.
3. **Restrained, Professional Clarity**: Avoid noisy AI design tropes. Deliver a clean, minimal light-mode interface where density, typography, and contrast serve rapid triage and evidence inspection.
4. **Resilient Failover**: If heavy neural models or local LLM instances lag or crash, deterministic regex heuristics and caching must instantly preserve system availability.

## Accessibility & Inclusion
- High contrast compliant with WCAG 2.1 AA standards for data tables, risk badges, and typography.
- Multi-lingual awareness: Hindi and English mixed transcription and legal references relevant to all Indian financial market participants.
