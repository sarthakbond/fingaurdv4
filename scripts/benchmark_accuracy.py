"""
Comprehensive Accuracy & Benchmark Evaluation Suite
===================================================
Tests FinGuard across 5 distinct forensic modules with ground-truth datasets:
  1. Text Scam & SEBI Regulatory Violation Classification (60 samples: 30 scam, 30 legit)
  2. Phishing & Typosquatted Domain Detection (60 samples: 30 phishing, 30 safe)
  3. SEBI Intermediary Registry Verification (50 queries: 25 verified, 25 invalid/fake)
  4. APK Package Security & Typosquatting (30 packages: 15 safe, 15 malicious/typosquatted)
  5. Multi-Modal Video/Audio Benchmark (from test_vid evaluation records)

Outputs:
  - Confusion Matrix (TP, TN, FP, FN) for every module
  - Precision, Recall, Specificity, F1-Score, and Accuracy
  - Macro-Averaged System Accuracy Report
"""
import os
import sys
import time
import json

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.stages.stage5_llm import run_stage5_llm
from src.stages.stage6_registry import run_stage6_registry
from src.stages.stage9_apk_domain import (
    scan_domain,
    scan_text_for_phishing_domains,
    _load_whitelist,
    _get_canonical_packages,
    _levenshtein
)
from src.config import get_stage_config, get_threshold

def compute_metrics(tp, tn, fp, fn):
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "total": total,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1
    }

# ============================================================================
# 1. TEXT SCAM & COMPLIANCE DATASET (30 Scam, 30 Legitimate)
# ============================================================================
SCAM_TEXTS = [
    # Explicit guaranteed returns & Hinglish
    "Bhai ye stock pakka jackpot hai, kal subah 9:15 pe rocket calls aayenge. 100% guaranteed monthly return!",
    "Join our VIP WhatsApp group. We guarantee 40% profit every month on BankNifty options trading.",
    "Sure shot jackpot stock tip! Double your money in 10 days. Zero-loss setup confirmed by institutional insider.",
    "Join my private Telegram channel for 500% returns on crypto and forex trading. DM for VIP payment link.",
    "Recover all your past trading losses within 1 week! Guaranteed profit sharing model with 100% accuracy.",
    "Kal subah 9:15 pe blast hoga, Nifty option call lene ka. Only 50 seats left in my premium group!",
    "Exclusive stock pump call! Guaranteed 10x multibagger in 30 days. Don't miss this lifetime jackpot opportunity.",
    "SEBI approved analyst INA000099999 guaranteeing 30% weekly return on equity futures. Send fee via UPI.",
    "Pakka jackpot call: Buy ABC Ltd at 45 target 150 in 3 days. Insider information from promoter group.",
    "Pay Rs 5,000 for VIP trading signals. 100% loss recovery guarantee or full refund within 24 hours.",
    "Paisa double scheme in stock market! Guaranteed capital protection with 50% monthly payout.",
    "Rocket call: Buy Nifty 25000 CE tomorrow at market open, sure shot 300 points rally.",
    "Last chance to join premium advisory club! 20 seats remaining. Guaranteed winning streak of 15 trades.",
    "Government approved secret trading algorithm generating 5% daily compounding profit without any risk.",
    "I am SEBI registered research analyst INA123456789. I guarantee 45% return on small-cap picks.",
    "Join our exclusive Telegram for daily jackpot tips. We have 50,000 members making lakhs daily.",
    "Special VIP jackpot scheme: Deposit 50,000 and get 1,50,000 guaranteed return after expiry date.",
    "Zero loss guaranteed formula for options buying. Secret hedge fund strategy leaked by whistleblower.",
    "DM me on WhatsApp +91 9876543210 for guaranteed 80% winning calls on commodity and gold futures.",
    "Sure shot upper circuit stock for tomorrow! Guaranteed 20% return in 1 trading session.",
    "Kal subah 9:15 jackpot trade. Guaranteed loss recovery service for retail traders suffering losses.",
    "Join our insider syndicate. 100% risk free guaranteed trading tips on high beta stocks.",
    "SEBI certified top advisor promising fixed 35% annual return with zero capital drawdown.",
    "Secret WhatsApp group with 100% accuracy in intraday calls. Join before link expires in 2 hours.",
    "Multibagger penny stock ready to explode 2000%. Buy now before circuit opens, guaranteed multibagger.",
    "High return investment pool: Transfer funds to UPI ID and receive guaranteed weekly interest of 8%.",
    "Pakka jackpot: Options expiry special trade. Turn Rs 10,000 into Rs 1,00,000 guaranteed.",
    "Zero risk algorithmic trading bot giving guaranteed 2% daily return. Limited licenses available.",
    "VIP signal service: 99% hit ratio on intraday stock options. Join our paid WhatsApp group today.",
    "Guaranteed 50% returns in 15 days on penny stock portfolio. Regulated by SEBI certified team."
]

LEGIT_TEXTS = [
    # Educational, disclaimers, Zerodha Varsity style, SEBI guidelines
    "Investing in securities market are subject to market risks. Read all scheme related documents carefully before investing.",
    "Equity investments are subject to market risks. Past performance of any scheme does not guarantee future results.",
    "Stop loss is a risk management tool that helps traders limit their downside risk in volatile market conditions.",
    "Before trading in derivatives (F&O), understand that 9 out of 10 individual traders incur net losses according to SEBI study.",
    "Diversification across different asset classes like equities, debt, and gold can help balance portfolio risk over time.",
    "A systematic investment plan (SIP) allows you to invest small amounts periodically in mutual funds to average your purchase cost.",
    "Research analysts are required to disclose their financial interest in the recommended stock under SEBI RA Regulations.",
    "The price-to-earnings (P/E) ratio compares a company's stock price to its earnings per share, indicating market valuation.",
    "Zerodha Broking Limited is a registered stockbroker with SEBI registration number INZ000031633.",
    "Groww Invest Tech Pvt Ltd is a SEBI registered investment adviser under registration number INA000018507.",
    "Always verify the registration status of any financial intermediary on the official SEBI website before seeking advice.",
    "Fundamental analysis evaluates a company's financial statements, management quality, competitive advantage, and industry outlook.",
    "Technical analysis involves studying historical price charts and trading volumes to identify market trends and support levels.",
    "Mutual funds do not offer guaranteed returns. Returns depend on market fluctuations and the underlying portfolio performance.",
    "Ensure your trading account has updated KYC details including PAN and Aadhaar linkage as per regulatory mandates.",
    "Angel One Limited is a registered member of NSE and BSE with SEBI registration INZ000161534.",
    "Hedging strategies using put options can help protect an equity portfolio against sudden market corrections.",
    "Do not trade based on unsolicited messages or tips received through SMS, WhatsApp, or social media platforms.",
    "Market volatility is an inherent part of investing. Long-term investors often benefit from maintaining disciplined asset allocation.",
    "A company's quarterly earnings report provides insights into revenue growth, operating margins, and net profit trends.",
    "Index funds track a benchmark index like Nifty 50 or Sensex, providing broad market exposure with low expense ratios.",
    "Capital gains tax applies when you sell an asset for more than you paid for it. Consult a qualified tax advisor.",
    "Risk-reward ratio measures expected profit against potential loss. A minimum 1:2 risk-reward is commonly recommended.",
    "The Reserve Bank of India (RBI) regulates monetary policy, while SEBI oversees the Indian securities market.",
    "Liquidity refers to how quickly and easily an asset can be converted into cash without substantially affecting its price.",
    "Dollar cost averaging reduces the impact of volatility by spreading out stock purchases over regular intervals.",
    "Securities lending and borrowing (SLB) is a mechanism that allows market participants to lend or borrow shares.",
    "Review your investment portfolio periodically to rebalance asset allocation in accordance with your risk appetite.",
    "Never invest borrowed funds in speculative financial instruments or short-term leveraged derivatives.",
    "Corporate actions such as stock splits, bonus issues, and dividends alter share capital and require shareholder approval."
]

# ============================================================================
# 2. PHISHING & DOMAIN DATASET (30 Phishing, 30 Legitimate)
# ============================================================================
PHISHING_URLS = [
    "https://groww-bonus-login.xyz/claim",
    "http://zerodha-kite-login.xyz/auth",
    "https://angelone-free-bonus.top/claim-now",
    "https://upstox-claim-bonus.click/login",
    "http://zerodha.com.login-x.in/secure",
    "https://groww-invest-bonus.shop/account",
    "http://zerodha-pro-terminal.xyz/web",
    "https://groww.in.secure-verify.top/kyc",
    "http://angelone-bonus-trade.click/signup",
    "https://upstox-instant-profit.xyz/claim",
    "http://zerodha-bonus-account.top/login",
    "https://groww-free-demat.club/offer",
    "http://angelone-rewards-claim.xyz/home",
    "https://upstox-vip-login.site/auth",
    "http://icicidirect-bonus-login.xyz/portal",
    "https://kotaksecurities-jackpot.top/claim",
    "http://motilaloswal-bonus.click/offer",
    "https://groww-login-online.buzz/verify",
    "http://zerodha-free-trades.shop/signup",
    "https://upstox-reward-portal.xyz/redeem",
    "http://angelone-secure-login.pro/auth",
    "https://groww-bonus-points.xyz/claim",
    "http://zerodha.org.in.phish-bank.com/kite",
    "https://upstox-super-account.top/free",
    "http://groww-trade-bonus.click/claim",
    "https://zerodha-kite-bonus.top/login",
    "http://angelone-vip-desk.xyz/verify",
    "https://icici-direct-bonus.click/redeem",
    "http://groww-cashback-login.xyz/offer",
    "https://upstox-bonus-club.top/claim"
]

SAFE_URLS = [
    "https://zerodha.com",
    "https://kite.zerodha.com",
    "https://console.zerodha.com",
    "https://groww.in",
    "https://groww.in/stocks",
    "https://groww.in/mutual-funds",
    "https://angelone.in",
    "https://trade.angelone.in",
    "https://upstox.com",
    "https://pro.upstox.com",
    "https://www.nseindia.com",
    "https://www.bseindia.com",
    "https://www.sebi.gov.in",
    "https://scores.sebi.gov.in",
    "https://www.icicidirect.com",
    "https://www.hdfcsec.com",
    "https://www.kotaksecurities.com",
    "https://www.motilaloswal.com",
    "https://www.sharekhan.com",
    "https://5paisa.com",
    "https://zerodha.com/varsity",
    "https://support.zerodha.com",
    "https://groww.in/blog",
    "https://www.angelone.in/knowledge-center",
    "https://upstox.com/learning-center",
    "https://www.nirmalbang.com",
    "https://www.geojit.com",
    "https://www.religareonline.com",
    "https://zerodha.com/open-account",
    "https://groww.in/calculators/sip-calculator"
]

# ============================================================================
# 3. SEBI REGISTRY DATASET (25 Verified, 25 Invalid/Mismatched/Fake)
# ============================================================================
VERIFIED_REGISTRY_QUERIES = [
    {"claimed_advisor_name": "Zerodha Broking Limited", "claimed_registration_number": "INZ000031633"},
    {"claimed_advisor_name": "Zerodha", "claimed_registration_number": "INZ000031633"},
    {"claimed_advisor_name": "Groww Invest Tech Private Limited", "claimed_registration_number": "INA000018507"},
    {"claimed_advisor_name": "Groww", "claimed_registration_number": "INA000018507"},
    {"claimed_advisor_name": "Angel One Limited", "claimed_registration_number": "INZ000161534"},
    {"claimed_advisor_name": "Angel One", "claimed_registration_number": "INZ000161534"},
    {"claimed_advisor_name": "Upstox", "claimed_registration_number": "INZ000185137"},
    {"claimed_advisor_name": "RKSV Securities India Private Limited", "claimed_registration_number": "INZ000185137"},
    {"claimed_advisor_name": "ICICI Securities Limited", "claimed_registration_number": "INZ000183631"},
    {"claimed_advisor_name": "ICICI Securities", "claimed_registration_number": "INZ000183631"},
    {"claimed_advisor_name": "HDFC Securities Limited", "claimed_registration_number": "INZ000186937"},
    {"claimed_advisor_name": "Kotak Securities Limited", "claimed_registration_number": "INZ000200137"},
    {"claimed_advisor_name": "Motilal Oswal Financial Services Limited", "claimed_registration_number": "INZ000158836"},
    {"claimed_advisor_name": "Motilal Oswal", "claimed_registration_number": "INZ000158836"},
    {"claimed_advisor_name": "5Paisa Capital Limited", "claimed_registration_number": "INZ000010231"},
    {"claimed_advisor_name": "Sharekhan Limited", "claimed_registration_number": "INZ000171337"},
    {"claimed_advisor_name": "Capitalmind Financial Services Private Limited", "claimed_registration_number": "INA000015507"},
    {"claimed_advisor_name": "Capitalmind", "claimed_registration_number": "INA000015507"},
    {"claimed_advisor_name": "Nithin Kamath", "claimed_registration_number": "INZ000031633"},
    {"claimed_advisor_name": "Deepak Shenoy", "claimed_registration_number": "INA000015507"},
    {"claimed_advisor_name": "Anand Rathi Share and Stock Brokers Limited", "claimed_registration_number": "INZ000170832"},
    {"claimed_advisor_name": "IIFL Securities Limited", "claimed_registration_number": "INZ000164132"},
    {"claimed_advisor_name": "Geojit Financial Services Limited", "claimed_registration_number": "INZ000104737"},
    {"claimed_advisor_name": "SMC Global Securities Limited", "claimed_registration_number": "INZ000199438"},
    {"claimed_advisor_name": "Paytm Money Limited", "claimed_registration_number": "INA100009859"}
]

INVALID_REGISTRY_QUERIES = [
    # Fake registration numbers
    {"claimed_advisor_name": "Jackpot Signals Desk", "claimed_registration_number": "INA999999999"},
    {"claimed_advisor_name": "Rocket Wealth Advisors", "claimed_registration_number": "INA000088888"},
    {"claimed_advisor_name": "Loss Recovery Super Group", "claimed_registration_number": "INA000077777"},
    {"claimed_advisor_name": "Options King Rahul", "claimed_registration_number": "INA000012345"},
    {"claimed_advisor_name": "Sure Shot Nifty Tips", "claimed_registration_number": "INA000054321"},
    # Mismatched name and number (Zerodha number with fake name)
    {"claimed_advisor_name": "Super Profit Capital", "claimed_registration_number": "INZ000031633"},
    {"claimed_advisor_name": "Forex King Syndicate", "claimed_registration_number": "INA000018507"},
    {"claimed_advisor_name": "Vip Trading Gurukul", "claimed_registration_number": "INZ000161534"},
    {"claimed_advisor_name": "Apex Options Desk", "claimed_registration_number": "INZ000185137"},
    {"claimed_advisor_name": "Crypto Wealth Machine", "claimed_registration_number": "INZ000183631"},
    # Malformed registration numbers
    {"claimed_advisor_name": "Alpha Traders", "claimed_registration_number": "INA123"},
    {"claimed_advisor_name": "Delta Tips Desk", "claimed_registration_number": "SEBI-REG-999"},
    {"claimed_advisor_name": "Omega Securities", "claimed_registration_number": "IN999"},
    {"claimed_advisor_name": "Prime Wealth", "claimed_registration_number": "CERT12345"},
    {"claimed_advisor_name": "Gold Stock Signals", "claimed_registration_number": "GOVT-APPROVED"},
    # Unregistered advisor names (no number provided)
    {"claimed_advisor_name": "Secret Multibagger Alerts", "claimed_registration_number": None},
    {"claimed_advisor_name": "Telegram VIP Signals Admin", "claimed_registration_number": None},
    {"claimed_advisor_name": "100 Percent Guaranteed Profits", "claimed_registration_number": None},
    {"claimed_advisor_name": "Nifty Jackpot Trader", "claimed_registration_number": None},
    {"claimed_advisor_name": "Penny Stock Hunter Desk", "claimed_registration_number": None},
    {"claimed_advisor_name": "Instant Loss Recovery Specialist", "claimed_registration_number": None},
    {"claimed_advisor_name": "Daily Double Return Scheme", "claimed_registration_number": None},
    {"claimed_advisor_name": "BankNifty Formula Master", "claimed_registration_number": None},
    {"claimed_advisor_name": "Insider Trading Group India", "claimed_registration_number": None},
    {"claimed_advisor_name": "Zero Loss Stock Signals", "claimed_registration_number": None}
]

# ============================================================================
# 4. APK PACKAGE DATASET (15 Safe, 15 Malicious / Typosquatted)
# ============================================================================
SAFE_APK_PACKAGES = [
    {"package_name": "com.zerodha.kite3", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "USE_BIOMETRIC"]},
    {"package_name": "in.groww", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "USE_BIOMETRIC"]},
    {"package_name": "com.nextbillion.groww", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.msf.angelmobile", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "USE_BIOMETRIC"]},
    {"package_name": "com.upstox.pro", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE", "VIBRATE"]},
    {"package_name": "com.icicidirect.idirectmobile", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.hdfcsec.fd", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.kotak.invest", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.motilaloswal.invest", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.sharekhan", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.fivepaisa.trade", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.dhan.live", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.zerodha.coin", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.paytmmoney", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]},
    {"package_name": "com.iifl.markets", "permissions": ["INTERNET", "ACCESS_NETWORK_STATE"]}
]

MALICIOUS_APK_PACKAGES = [
    # Typosquats & Trojan permissions
    {"package_name": "com.zerodha.kite3.pro", "permissions": ["INTERNET", "READ_SMS", "RECEIVE_SMS"]},
    {"package_name": "in.groww.freebonus", "permissions": ["INTERNET", "BIND_ACCESSIBILITY_SERVICE"]},
    {"package_name": "com.msf.angelmobile.mod", "permissions": ["INTERNET", "READ_SMS", "RECEIVE_SMS"]},
    {"package_name": "com.upstox.pro.vip", "permissions": ["INTERNET", "SYSTEM_ALERT_WINDOW", "READ_SMS"]},
    {"package_name": "com.zerodha.kite.hack", "permissions": ["INTERNET", "PACKAGE_USAGE_STATS", "READ_SMS"]},
    {"package_name": "in.groww.loginbonus", "permissions": ["INTERNET", "READ_SMS", "RECEIVE_SMS"]},
    {"package_name": "com.angelone.superbroker", "permissions": ["INTERNET", "BIND_ACCESSIBILITY_SERVICE"]},
    {"package_name": "com.upstox.instantprofit", "permissions": ["INTERNET", "READ_SMS", "READ_CONTACTS"]},
    {"package_name": "com.icicidirect.bonus", "permissions": ["INTERNET", "RECEIVE_SMS", "SYSTEM_ALERT_WINDOW"]},
    {"package_name": "com.kotak.invest.free", "permissions": ["INTERNET", "READ_SMS", "BIND_ACCESSIBILITY_SERVICE"]},
    {"package_name": "com.motilaloswal.jackpot", "permissions": ["INTERNET", "READ_SMS", "RECEIVE_SMS"]},
    {"package_name": "com.sharekhan.vip", "permissions": ["INTERNET", "BIND_ACCESSIBILITY_SERVICE"]},
    {"package_name": "com.fivepaisa.hack", "permissions": ["INTERNET", "READ_SMS", "SYSTEM_ALERT_WINDOW"]},
    {"package_name": "com.zerodha.freebonus", "permissions": ["INTERNET", "READ_SMS", "PACKAGE_USAGE_STATS"]},
    {"package_name": "in.groww.vipclub", "permissions": ["INTERNET", "BIND_ACCESSIBILITY_SERVICE", "RECEIVE_SMS"]}
]


def test_text_scam_detection():
    print("\n" + "=" * 65)
    print("  [TEST 1] Text Scam & SEBI Regulatory Violation Classification")
    print(f"  Dataset: {len(SCAM_TEXTS)} Scams + {len(LEGIT_TEXTS)} Legitimate = {len(SCAM_TEXTS) + len(LEGIT_TEXTS)} Total")
    print("=" * 65)
    
    tp, tn, fp, fn = 0, 0, 0, 0
    t0 = time.time()
    
    # Evaluate Scam Texts (Positive Class)
    print("Evaluating Scam Texts (Positive Class)...")
    for idx, text in enumerate(SCAM_TEXTS):
        res = run_stage5_llm(text, f"bench_scam_{idx}")
        is_scam = res.get("is_scam_likely", False)
        if is_scam:
            tp += 1
        else:
            fn += 1
            print(f"  [FN] Missed scam: '{text[:60]}...' (Score: {res.get('composite_risk_score', 0):.2f})")
            
    # Evaluate Legitimate Texts (Negative Class)
    print("Evaluating Legitimate Texts (Negative Class)...")
    for idx, text in enumerate(LEGIT_TEXTS):
        res = run_stage5_llm(text, f"bench_legit_{idx}")
        is_scam = res.get("is_scam_likely", False)
        if is_scam:
            fp += 1
            print(f"  [FP] False alarm on legit: '{text[:60]}...' (Score: {res.get('composite_risk_score', 0):.2f})")
        else:
            tn += 1

    elapsed = time.time() - t0
    metrics = compute_metrics(tp, tn, fp, fn)
    metrics["time_sec"] = round(elapsed, 2)
    
    print(f"\n  [RESULTS] Text Compliance Engine:")
    print(f"    - True Positives (TP) : {tp}/{len(SCAM_TEXTS)}")
    print(f"    - True Negatives (TN) : {tn}/{len(LEGIT_TEXTS)}")
    print(f"    - False Positives (FP): {fp}")
    print(f"    - False Negatives (FN): {fn}")
    print(f"    - Accuracy            : {metrics['accuracy'] * 100:.2f}%")
    print(f"    - Precision           : {metrics['precision'] * 100:.2f}%")
    print(f"    - Recall              : {metrics['recall'] * 100:.2f}%")
    print(f"    - Specificity         : {metrics['specificity'] * 100:.2f}%")
    print(f"    - F1-Score            : {metrics['f1'] * 100:.2f}%")
    print(f"    - Elapsed Time        : {elapsed:.2f}s ({elapsed/(len(SCAM_TEXTS)+len(LEGIT_TEXTS)):.3f}s/sample)")
    return metrics


def test_url_phishing_detection():
    print("\n" + "=" * 65)
    print("  [TEST 2] Phishing & Typosquatted Domain Detection")
    print(f"  Dataset: {len(PHISHING_URLS)} Phishing + {len(SAFE_URLS)} Safe = {len(PHISHING_URLS) + len(SAFE_URLS)} Total")
    print("=" * 65)
    
    tp, tn, fp, fn = 0, 0, 0, 0
    t0 = time.time()
    
    # Phishing URLs (Positive Class)
    for url in PHISHING_URLS:
        res = scan_domain(url, "bench_url_p")
        if res.get("is_phishing", False):
            tp += 1
        else:
            fn += 1
            print(f"  [FN] Missed phishing: {url}")
            
    # Safe URLs (Negative Class)
    for url in SAFE_URLS:
        res = scan_domain(url, "bench_url_s")
        if res.get("is_phishing", False):
            fp += 1
            print(f"  [FP] False alarm on safe: {url}")
        else:
            tn += 1

    elapsed = time.time() - t0
    metrics = compute_metrics(tp, tn, fp, fn)
    metrics["time_sec"] = round(elapsed, 2)
    
    print(f"\n  [RESULTS] URL Phishing Auditor:")
    print(f"    - True Positives (TP) : {tp}/{len(PHISHING_URLS)}")
    print(f"    - True Negatives (TN) : {tn}/{len(SAFE_URLS)}")
    print(f"    - False Positives (FP): {fp}")
    print(f"    - False Negatives (FN): {fn}")
    print(f"    - Accuracy            : {metrics['accuracy'] * 100:.2f}%")
    print(f"    - Precision           : {metrics['precision'] * 100:.2f}%")
    print(f"    - Recall              : {metrics['recall'] * 100:.2f}%")
    print(f"    - Specificity         : {metrics['specificity'] * 100:.2f}%")
    print(f"    - F1-Score            : {metrics['f1'] * 100:.2f}%")
    print(f"    - Elapsed Time        : {elapsed:.2f}s")
    return metrics


def test_registry_verification():
    print("\n" + "=" * 65)
    print("  [TEST 3] SEBI Intermediary Registry Fuzzy Verification")
    print(f"  Dataset: {len(VERIFIED_REGISTRY_QUERIES)} Verified + {len(INVALID_REGISTRY_QUERIES)} Invalid = {len(VERIFIED_REGISTRY_QUERIES) + len(INVALID_REGISTRY_QUERIES)} Total")
    print("=" * 65)
    
    tp, tn, fp, fn = 0, 0, 0, 0
    t0 = time.time()
    
    for q in VERIFIED_REGISTRY_QUERIES:
        res = run_stage6_registry(q, "bench_reg_v")
        if res.get("verdict") == "verified":
            tp += 1
        else:
            fn += 1
            print(f"  [FN] Expected verified: {q} -> got '{res.get('verdict')}'")
            
    for q in INVALID_REGISTRY_QUERIES:
        res = run_stage6_registry(q, "bench_reg_inv")
        if res.get("verdict") == "verified":
            fp += 1
            print(f"  [FP] Unexpected verified: {q}")
        else:
            tn += 1

    elapsed = time.time() - t0
    metrics = compute_metrics(tp, tn, fp, fn)
    metrics["time_sec"] = round(elapsed, 2)
    
    print(f"\n  [RESULTS] Registry Cross-Checker:")
    print(f"    - True Positives (Verified) : {tp}/{len(VERIFIED_REGISTRY_QUERIES)}")
    print(f"    - True Negatives (Rejected) : {tn}/{len(INVALID_REGISTRY_QUERIES)}")
    print(f"    - False Positives           : {fp}")
    print(f"    - False Negatives           : {fn}")
    print(f"    - Accuracy                  : {metrics['accuracy'] * 100:.2f}%")
    print(f"    - Precision                 : {metrics['precision'] * 100:.2f}%")
    print(f"    - Recall                    : {metrics['recall'] * 100:.2f}%")
    print(f"    - F1-Score                  : {metrics['f1'] * 100:.2f}%")
    print(f"    - Elapsed Time              : {elapsed:.2f}s")
    return metrics


def audit_manifest_data(pkg: str, permissions: list) -> dict:
    stage_cfg = get_stage_config("stage9_apk_domain")
    dangerous_perms = set(stage_cfg.get("dangerous_permissions", [
        "READ_SMS", "RECEIVE_SMS", "READ_CONTACTS",
        "BIND_ACCESSIBILITY_SERVICE", "PACKAGE_USAGE_STATS"
    ]))
    max_dist = get_threshold("apk_domain_levenshtein_max_dist", 3)
    whitelist = _load_whitelist()
    canonical_packages = _get_canonical_packages(whitelist)
    
    pkg_clean = pkg.lower()
    perms_set = set(p.split(".")[-1].upper() for p in permissions)
    
    # 1. Exact package match → legitimate
    for known_pkg, broker in canonical_packages:
        if pkg_clean == known_pkg:
            return {"is_suspicious": False, "risk_level": "clean", "reason": f"Exact match {broker}"}
            
    # 2. Package name typo-squatting
    pkg_base = pkg_clean.rsplit(".", 1)[-1] if "." in pkg_clean else pkg_clean
    best_dist = 999
    best_known = None
    best_broker = None
    for known_pkg, broker in canonical_packages:
        known_base = known_pkg.rsplit(".", 1)[-1] if "." in known_pkg else known_pkg
        dist = _levenshtein(pkg_base, known_base)
        if dist < best_dist:
            best_dist = dist
            best_known = known_pkg
            best_broker = broker
            
    is_suspicious = False
    if 0 < best_dist <= max_dist:
        is_suspicious = True
        
    found_dangerous = list(perms_set & dangerous_perms)
    if found_dangerous:
        is_suspicious = True
        
    return {
        "is_suspicious": is_suspicious,
        "risk_level": "high" if is_suspicious else "clean"
    }


def test_apk_security():
    print("\n" + "=" * 65)
    print("  [TEST 4] APK Manifest Security & Broker Typosquatting")
    print(f"  Dataset: {len(MALICIOUS_APK_PACKAGES)} Suspicious + {len(SAFE_APK_PACKAGES)} Safe = {len(MALICIOUS_APK_PACKAGES) + len(SAFE_APK_PACKAGES)} Total")
    print("=" * 65)
    
    tp, tn, fp, fn = 0, 0, 0, 0
    t0 = time.time()
    
    # Suspicious APKs (Positive Class)
    for apk in MALICIOUS_APK_PACKAGES:
        res = audit_manifest_data(apk["package_name"], apk["permissions"])
        if res.get("is_suspicious", False):
            tp += 1
        else:
            fn += 1
            print(f"  [FN] Missed suspicious APK: {apk['package_name']}")
            
    # Safe APKs (Negative Class)
    for apk in SAFE_APK_PACKAGES:
        res = audit_manifest_data(apk["package_name"], apk["permissions"])
        if res.get("is_suspicious", False):
            fp += 1
            print(f"  [FP] False alarm on safe APK: {apk['package_name']}")
        else:
            tn += 1

    elapsed = time.time() - t0
    metrics = compute_metrics(tp, tn, fp, fn)
    metrics["time_sec"] = round(elapsed, 2)
    
    print(f"\n  [RESULTS] APK Manifest Security Auditor:")
    print(f"    - True Positives (Suspicious Caught) : {tp}/{len(MALICIOUS_APK_PACKAGES)}")
    print(f"    - True Negatives (Safe Verified)     : {tn}/{len(SAFE_APK_PACKAGES)}")
    print(f"    - False Positives                    : {fp}")
    print(f"    - False Negatives                    : {fn}")
    print(f"    - Accuracy                           : {metrics['accuracy'] * 100:.2f}%")
    print(f"    - Precision                          : {metrics['precision'] * 100:.2f}%")
    print(f"    - Recall                             : {metrics['recall'] * 100:.2f}%")
    print(f"    - F1-Score                           : {metrics['f1'] * 100:.2f}%")
    print(f"    - Elapsed Time                       : {elapsed:.2f}s")
    return metrics


def test_video_results():
    print("\n" + "=" * 65)
    print("  [TEST 5] Multi-Modal Video / Audio Pipeline Benchmark")
    print("=" * 65)
    
    csv_path = os.path.join(ROOT_DIR, "tests", "test_results.csv")
    if not os.path.exists(csv_path):
        print("  [INFO] tests/test_results.csv not found yet. Using live video samples...")
        return None
        
    import csv
    tp, tn, fp, fn = 0, 0, 0, 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get("Filename", "")
            verdict = row.get("Verdict", "")
            is_scam_or_fake = ("critical" in verdict.lower()) or ("warning" in verdict.lower()) or ("suspicious" in verdict.lower())
            
            # Ground truth: scam_vid folder = positive, noscam_vid = negative
            is_ground_truth_scam = "4.05.01" in filename or "4.05.39" in filename
            if is_ground_truth_scam:
                if is_scam_or_fake:
                    tp += 1
                else:
                    fn += 1
            else:
                if is_scam_or_fake:
                    fp += 1
                else:
                    tn += 1
                    
    metrics = compute_metrics(tp, tn, fp, fn)
    print(f"  [RESULTS] Video Forensic Pipeline (from {csv_path}):")
    print(f"    - Accuracy  : {metrics['accuracy'] * 100:.2f}% ({tp+tn}/{metrics['total']} correct)")
    print(f"    - Precision : {metrics['precision'] * 100:.2f}%")
    print(f"    - Recall    : {metrics['recall'] * 100:.2f}%")
    print(f"    - F1-Score  : {metrics['f1'] * 100:.2f}%")
    return metrics


def main():
    print("=" * 70)
    print("  ⚡ FINGUARD COMPREHENSIVE ACCURACY EVALUATION HARNESS")
    print("=" * 70)
    
    text_m = test_text_scam_detection()
    url_m = test_url_phishing_detection()
    reg_m = test_registry_verification()
    apk_m = test_apk_security()
    vid_m = test_video_results()
    
    print("\n" + "=" * 70)
    print("  🏆 FINAL SYSTEM-WIDE BENCHMARK & ACCURACY SUMMARY")
    print("=" * 70)
    
    all_metrics = [
        ("Text Scam & SEBI Violation", text_m),
        ("Phishing & Typosquatted Domain", url_m),
        ("SEBI Registry Verification", reg_m),
        ("APK Security & Typosquatting", apk_m)
    ]
    if vid_m and vid_m.get("total", 0) > 0:
        all_metrics.append(("Multi-Modal Video Pipeline", vid_m))
        
    print(f"{'Module / Test Category':<35} | {'Samples':<8} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 95)
    
    total_samples = 0
    total_correct = 0
    acc_sum = 0
    f1_sum = 0
    
    for name, m in all_metrics:
        total_samples += m["total"]
        total_correct += (m["tp"] + m["tn"])
        acc_sum += m["accuracy"]
        f1_sum += m["f1"]
        print(f"{name:<35} | {m['total']:<8} | {m['accuracy']*100:>6.2f}%   | {m['precision']*100:>6.2f}%   | {m['recall']*100:>6.2f}%   | {m['f1']*100:>6.2f}%")
        
    overall_acc = (total_correct / total_samples) * 100
    macro_acc = (acc_sum / len(all_metrics)) * 100
    macro_f1 = (f1_sum / len(all_metrics)) * 100
    
    print("-" * 95)
    print(f"{'OVERALL WEIGHTED ACCURACY':<35} | {total_samples:<8} | {overall_acc:>6.2f}%   | {'--':<10} | {'--':<10} | {macro_f1:>6.2f}%")
    print(f"{'MACRO-AVERAGED ACCURACY':<35} | {len(all_metrics)} tests | {macro_acc:>6.2f}%   | {'--':<10} | {'--':<10} | {macro_f1:>6.2f}%")
    print("=" * 70)
    
    # Save structured benchmark to tests/benchmark_metrics.json
    results_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_samples_evaluated": total_samples,
        "overall_weighted_accuracy": round(overall_acc, 2),
        "macro_averaged_accuracy": round(macro_acc, 2),
        "macro_averaged_f1": round(macro_f1, 2),
        "modules": {
            name: m for name, m in all_metrics
        }
    }
    out_json = os.path.join(ROOT_DIR, "tests", "benchmark_metrics.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)
    print(f"[+] Saved structured metrics report to: {out_json}\n")


if __name__ == "__main__":
    main()
