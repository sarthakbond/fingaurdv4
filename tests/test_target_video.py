import requests
import time
import json

url = "http://localhost:8000/api/jobs"
vid_path = r"test_vid/scam_vid/WhatsApp Video 2026-08-26 at 4.05.39 PM.mp4"

with open(vid_path, "rb") as f:
    resp = requests.post(url, files={"file": f}, data={"mode": "video"})

print("Submit status:", resp.status_code)
data = resp.json()
job_id = data["job_id"]
print("Job ID:", job_id)

while True:
    time.sleep(2)
    poll_resp = requests.get(f"{url}/{job_id}").json()
    status = poll_resp.get("status")
    print(f"Polling {job_id}: {status}")
    if status in ("completed", "complete", "failed"):
        break

print("\n================== FULL RESULT ==================")
print("Verdict:", poll_resp.get("verdict"))
print("Is Scam:", poll_resp.get("is_scam"))
print("Composite Risk:", poll_resp.get("composite_risk_score"))
sebi = poll_resp.get("sebi_analysis", {})
print("Engine:", sebi.get("analysis_engine"))
print("Fallback reason:", sebi.get("fallback_reason"))
print("Signal scores:", json.dumps(sebi.get("signal_scores", {}), indent=2))
print("Reasoning:", sebi.get("reasoning"))
print("Implied returns:", sebi.get("implied_returns"))
print("Urgency/Scarcity:", sebi.get("urgency_scarcity_language"))
print("Paywall push:", sebi.get("paywall_push"))
print("Transcript:", poll_resp.get("transcript"))
print("=================================================")
