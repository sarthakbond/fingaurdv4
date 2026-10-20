import urllib.request
import urllib.parse
import json

def test_registry_frontend_integration():
    # 1. Verify index.html contains all required elements
    html_url = "http://127.0.0.1:8000/"
    with urllib.request.urlopen(html_url, timeout=5) as response:
        html = response.read().decode("utf-8")
    
    assert "registry-directory-section" in html, "Missing registry-directory-section in HTML"
    assert "top-db-count" in html, "Missing top-db-count in HTML"
    assert "registry-search-input" in html, "Missing registry-search-input in HTML"
    assert "stat-total-records" in html, "Missing stat-total-records in HTML"
    assert "stat-ra" in html, "Missing stat-ra in HTML"
    assert "stat-ria" in html, "Missing stat-ria in HTML"
    assert "stat-brokers" in html, "Missing stat-brokers in HTML"
    assert "stat-pms" in html, "Missing stat-pms in HTML"
    assert "stat-mf" in html, "Missing stat-mf in HTML"
    assert "registry-results-container" in html, "Missing registry-results-container in HTML"
    print("PASS: static/index.html contains all SEBI registry elements.")

    # 2. Verify banking.css contains registry styles
    css_url = "http://127.0.0.1:8000/static/css/banking.css"
    with urllib.request.urlopen(css_url, timeout=5) as response:
        css = response.read().decode("utf-8")
    
    assert ".fg-registry-hero-card" in css, "Missing .fg-registry-hero-card in CSS"
    assert ".fg-registry-stats-grid" in css, "Missing .fg-registry-stats-grid in CSS"
    assert ".fg-reg-card" in css, "Missing .fg-reg-card in CSS"
    assert ".fg-pulse-dot" in css, "Missing .fg-pulse-dot in CSS"
    print("PASS: static/css/banking.css contains all registry showcase styles.")

    # 3. Verify main.js contains registry showcase initialization and handlers
    js_url = "http://127.0.0.1:8000/static/js/main.js"
    with urllib.request.urlopen(js_url, timeout=5) as response:
        js = response.read().decode("utf-8")
    
    assert "initRegistryShowcase" in js, "Missing initRegistryShowcase in main.js"
    assert "registryStatus" in js, "Missing registryStatus in main.js"
    assert "registrySearch" in js, "Missing registrySearch in main.js"
    print("PASS: static/js/main.js contains initRegistryShowcase and live search wiring.")

    # 4. Verify API status endpoint
    status_url = "http://127.0.0.1:8000/api/registry/status"
    with urllib.request.urlopen(status_url, timeout=5) as response:
        status_data = json.loads(response.read().decode("utf-8"))
    
    assert status_data.get("total_records") == 4709, f"Unexpected total_records: {status_data.get('total_records')}"
    breakdown = status_data.get("registry_breakdown", {})
    assert len(breakdown) > 0, "Empty registry breakdown"
    print(f"PASS: /api/registry/status returned {status_data.get('total_records')} total records.")

    # 5. Verify API search endpoint for entities, brokers, contact persons
    test_queries = ["Zerodha", "Kotak", "INA000016171", "Mayank"]
    for q in test_queries:
        search_url = f"http://127.0.0.1:8000/api/registry/search?q={urllib.parse.quote(q)}"
        with urllib.request.urlopen(search_url, timeout=5) as response:
            search_data = json.loads(response.read().decode("utf-8"))
        matches = search_data.get("total_matches", 0)
        assert matches > 0, f"Expected matches for '{q}', got 0"
        results = search_data.get("results", [])
        assert len(results) > 0, f"Expected non-empty results for '{q}'"
        first = results[0]
        assert "registration_number" in first, "Missing registration_number in result"
        assert "name" in first, "Missing name in result"
        print(f"PASS: Search query '{q}' matched {matches} records (First: {first['name']} - {first['registration_number']}).")

if __name__ == "__main__":
    test_registry_frontend_integration()
    print("\nALL SEBI REGISTRY FRONTEND INTEGRATION TESTS PASSED SUCCESSFULLY!")
