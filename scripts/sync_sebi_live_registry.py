"""
Comprehensive SEBI Live Registry Ingestion Engine
Fetches officially registered intermediaries directly from SEBI's portal:
- Investment Advisers (RIAs)
- Research Analysts (RAs)
- Portfolio Managers (PMS)
- Stock Brokers
- Mutual Funds
Extracts both legal entity names and individual people names (Contact Persons).
"""
import urllib.request
import urllib.parse
import http.cookiejar
import ssl
import re
import html as html_lib
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

SEBI_AJAX_URL = "https://www.sebi.gov.in/sebiweb/ajax/other/getintmfpiinfo.jsp"
SEBI_HOME_URL = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId="

CATEGORIES = [
    {"name": "Investment Adviser", "intmId": "13", "max_pages": 45},
    {"name": "Research Analyst", "intmId": "14", "max_pages": 95},
    {"name": "Portfolio Manager", "intmId": "33", "max_pages": 25},
    {"name": "Mutual Fund", "intmId": "23", "max_pages": 5},
    {"name": "Stock Broker", "intmId": "30", "max_pages": 50},
]

def create_session(intm_id):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=ctx)
    )
    init_url = f"{SEBI_HOME_URL}{intm_id}"
    req = urllib.request.Request(
        init_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    try:
        with opener.open(req, timeout=15) as r:
            _ = r.read()
    except Exception as e:
        print(f"Warning: Session init failed for intmId={intm_id}: {e}")
    return opener, init_url

def clean_text(text):
    if not text:
        return ""
    text = html_lib.unescape(text)
    text = text.replace("&#64;", "@").replace("&#46;", ".").replace("&amp;", "&")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_card(card_html, category_name):
    # Extract Name
    name_m = re.search(r'Name</span></div><div class=[\'"]value[^\'"]*[\'"]><span>([\s\S]*?)</span>', card_html, re.IGNORECASE)
    # Extract Registration No.
    reg_m = re.search(r'Registration No\.</span></div><div class=[\'"]value[^\'"]*[\'"]><span>([\s\S]*?)</span>', card_html, re.IGNORECASE)
    # Extract Contact Person
    person_m = re.search(r'Contact Person</span></div><div class=[\'"]value[^\'"]*[\'"]><span>([\s\S]*?)</span>', card_html, re.IGNORECASE)
    # Extract Validity
    val_m = re.search(r'Validity</span></div><div class=[\'"]value[^\'"]*[\'"]><span>([\s\S]*?)</span>', card_html, re.IGNORECASE)

    if not name_m or not reg_m:
        return None

    raw_name = clean_text(name_m.group(1))
    raw_reg = clean_text(reg_m.group(1)).replace(" ", "").upper()
    raw_person = clean_text(person_m.group(1)) if person_m else ""
    raw_val = clean_text(val_m.group(1)) if val_m else "Active"

    if not raw_name or not raw_reg or len(raw_reg) < 6:
        return None

    # Filter out bogus entries
    if any(b in raw_name.lower() for b in ["registered intermediaries", "schemes", "select intermediary"]):
        return None

    aliases = [raw_name]
    if raw_person and raw_person.lower() != raw_name.lower():
        aliases.append(raw_person)
    
    # Also extract person name from "Name" if format is "Person Name Proprietor of Entity Name"
    prop_m = re.search(r'^(.*?)\s*Proprietor\s*(?:of)?\s*(.*)$', raw_name, re.IGNORECASE)
    if prop_m:
        p_name = prop_m.group(1).strip(" -:,")
        e_name = prop_m.group(2).strip(" -:,")
        if p_name and p_name not in aliases:
            aliases.append(p_name)
        if e_name and e_name not in aliases:
            aliases.append(e_name)

    # Clean duplicates in aliases
    unique_aliases = []
    seen_alias = set()
    for a in aliases:
        norm = a.strip().lower()
        if norm and norm not in seen_alias and len(norm) > 2:
            seen_alias.add(norm)
            unique_aliases.append(a.strip())

    return {
        "name": raw_name,
        "aliases": unique_aliases,
        "registration_number": raw_reg,
        "type": category_name,
        "status": "Active" if ("perpetual" in raw_val.lower() or "valid" in raw_val.lower() or "active" in raw_val.lower() or not raw_val) else raw_val,
        "contact_person": raw_person if raw_person else None
    }

def fetch_page(opener, init_url, intm_id, category_name, page_num):
    data = {
        "nextValue": str(page_num),
        "next": "n",
        "intmId": str(intm_id),
        "contPer": "",
        "name": "",
        "regNo": "",
        "email": "",
        "location": "",
        "exchange": "",
        "affiliate": "",
        "alp": "",
        "doDirect": str(page_num),
        "intmIds": ""
    }
    req = urllib.request.Request(
        SEBI_AJAX_URL,
        data=urllib.parse.urlencode(data).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": init_url,
            "X-Requested-With": "XMLHttpRequest"
        }
    )
    for attempt in range(3):
        try:
            with opener.open(req, timeout=12) as r:
                html = r.read().decode("utf-8", errors="ignore")
            
            # Split into card chunks
            chunks = re.split(r'<div class=[\'"]card-table-left', html)
            page_records = []
            for c in chunks[1:]:
                rec = parse_card(c, category_name)
                if rec:
                    page_records.append(rec)
            return page_records
        except Exception as e:
            if attempt == 2:
                print(f"Failed page {page_num} for {category_name}: {e}")
            time.sleep(1)
    return []

def scrape_category(cat_info):
    cat_name = cat_info["name"]
    intm_id = cat_info["intmId"]
    max_pages = cat_info["max_pages"]
    
    print(f"\n>>> Starting ingest for [{cat_name}] (intmId={intm_id}, target {max_pages} pages)...")
    opener, init_url = create_session(intm_id)
    
    # First check page 0 (or page 1) to inspect total pages
    first_page_records = fetch_page(opener, init_url, intm_id, cat_name, 0)
    all_cat_records = {r["registration_number"]: r for r in first_page_records}
    print(f"[{cat_name}] Page 1 extracted {len(first_page_records)} records")

    # Fetch subsequent pages
    for page in range(1, max_pages):
        records = fetch_page(opener, init_url, intm_id, cat_name, page)
        if not records:
            # Reached end or empty page
            print(f"[{cat_name}] Page {page + 1} returned 0 records. Ending category pagination.")
            break
        for r in records:
            all_cat_records[r["registration_number"]] = r
        if (page + 1) % 10 == 0 or page == max_pages - 1:
            print(f"[{cat_name}] Progress: Page {page + 1}/{max_pages} -> Total so far: {len(all_cat_records)}")
        time.sleep(0.15) # Polite delay

    print(f"[{cat_name}] Completed! Extracted {len(all_cat_records)} verified records.")
    return all_cat_records

def main():
    start_time = time.time()
    existing_file = "static_data/sebi_registry.json"
    existing_db = {}
    if os.path.exists(existing_file):
        try:
            with open(existing_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    existing_db[item["registration_number"]] = item
            print(f"Loaded {len(existing_db)} existing records from {existing_file}")
        except Exception as e:
            print(f"Warning: Could not read existing file: {e}")

    total_fetched = {}
    for cat in CATEGORIES:
        cat_records = scrape_category(cat)
        total_fetched.update(cat_records)

    print(f"\n=== SCRAPE COMPLETE ===")
    print(f"Total verified entities pulled from SEBI: {len(total_fetched)}")

    # Merge into existing DB
    merged_count = 0
    updated_count = 0
    new_count = 0

    for reg_no, rec in total_fetched.items():
        if reg_no in existing_db:
            # Preserve existing custom aliases, add new ones
            existing = existing_db[reg_no]
            combined_aliases = list(set(existing.get("aliases", []) + rec.get("aliases", [])))
            existing["aliases"] = combined_aliases
            if "contact_person" in rec and rec["contact_person"]:
                existing["contact_person"] = rec["contact_person"]
            updated_count += 1
        else:
            existing_db[reg_no] = rec
            new_count += 1

    final_list = list(existing_db.values())
    # Sort cleanly by registration number
    final_list.sort(key=lambda x: (x.get("type", ""), x.get("registration_number", "")))

    with open(existing_file, "w", encoding="utf-8") as f:
        json.dump(final_list, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - start_time
    print(f"\n=== DATABASE UPDATE COMPLETE ===")
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"New entities added: {new_count}")
    print(f"Existing entities enriched: {updated_count}")
    print(f"Total database count in {existing_file}: {len(final_list)}")

if __name__ == "__main__":
    main()
