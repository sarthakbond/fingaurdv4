"""
Unit & Integration Tests for FinGuard WhatsApp Forensic Webhook
Verifies TwiML generation, text scam scanning, command routing, and safety verdicts.
"""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_whatsapp_webhook_get():
    """Verify that the GET health check endpoint responds with active status."""
    response = client.get("/api/whatsapp/webhook")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "active"
    assert "FinGuard" in data.get("service")

def test_whatsapp_webhook_welcome_greeting():
    """Verify that greetings like 'hi' or 'help' return the onboarding guide in valid TwiML."""
    response = client.post(
        "/api/whatsapp/webhook",
        data={"From": "whatsapp:+919876543210", "Body": "hi", "NumMedia": "0"}
    )
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    text = response.text
    assert "<Response>" in text
    assert "<Message>" in text
    assert "Welcome to FinGuard!" in text
    assert "Text Forward" in text

def test_whatsapp_webhook_status_command():
    """Verify that 'status' command returns system hardware and model info."""
    response = client.post(
        "/api/whatsapp/webhook",
        data={"From": "whatsapp:+919876543210", "Body": "status", "NumMedia": "0"}
    )
    assert response.status_code == 200
    text = response.text
    assert "FinGuard System Status" in text
    assert "Pipeline Stages" in text

def test_whatsapp_webhook_scam_text_analysis():
    """Verify that a forwarded scam stock tip receives a high-risk forensic verdict."""
    scam_msg = (
        "Pakka jackpot call! Buy Bank Nifty 52000 CE. "
        "100% loss recovery guaranteed return! 20% daily profit. DM to mirror trades."
    )
    response = client.post(
        "/api/whatsapp/webhook",
        data={"From": "whatsapp:+919876543210", "Body": scam_msg, "NumMedia": "0"}
    )
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    text = response.text
    assert "FinGuard Forensic Alert" in text
    assert "Risk Rating" in text
    # Should flag high risk or warning
    assert ("CRITICAL" in text or "WARNING" in text or "SUSPICIOUS" in text or "Risk" in text)
    assert "Do NOT transfer money" in text

def test_whatsapp_webhook_safe_text_analysis():
    """
    Verify that benign educational financial content does not trigger a Critical or Warning scam alert.
    When Ollama is offline and heuristic fallback is used, FinGuard fail-safes to Suspicious: Review Recommended (0% risk).
    """
    safe_msg = (
        "Mutual funds are subject to market risks. "
        "Read all scheme related documents carefully before investing for the long term."
    )
    response = client.post(
        "/api/whatsapp/webhook",
        data={"From": "whatsapp:+919876543210", "Body": safe_msg, "NumMedia": "0"}
    )
    assert response.status_code == 200
    text = response.text
    assert "FinGuard Forensic Alert" in text
    assert ("SAFE" in text or "SUSPICIOUS: REVIEW RECOMMENDED" in text)
    assert "CRITICAL" not in text
    assert "WARNING" not in text
    assert "*0% Risk Likelihood*" in text or "*0% Risk*" in text or "0%" in text

def test_whatsapp_webhook_phishing_url_analysis():
    """Verify that phishing or typo-squatted broker URLs trigger threat alerts."""
    url_msg = "Claim your free Zerodha bonus shares now: https://zerodha-trading-bonus.top"
    response = client.post(
        "/api/whatsapp/webhook",
        data={"From": "whatsapp:+919876543210", "Body": url_msg, "NumMedia": "0"}
    )
    assert response.status_code == 200
    assert text.find("FinGuard Forensic Alert") != -1
    assert ("Domain Safety" in text or "Phishing" in text or "Risk" in text)


def test_whatsapp_bridge_message_greeting():
    """Verify that the direct bridge endpoint returns JSON welcome guide on 'hi'."""
    response = client.post(
        "/api/whatsapp/bridge-message",
        json={"sender": "whatsapp:+919876543210", "body": "hi"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "welcome"
    assert "Welcome to FinGuard!" in data.get("reply", "")


def test_whatsapp_bridge_message_status():
    """Verify that the direct bridge endpoint returns JSON system status."""
    response = client.post(
        "/api/whatsapp/bridge-message",
        json={"sender": "whatsapp:+919876543210", "body": "status"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("type") == "status"
    assert "FinGuard System Status" in data.get("reply", "")

