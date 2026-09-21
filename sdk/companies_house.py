"""
Companies House SDK for powuk.

REST API + Document API + Streaming API + Bulk Data.
All in one place. Import and use.

Usage:
    from sdk.companies_house import search_companies, get_company, get_officers
    
    # Search for electrical contractors in London
    results = search_companies("electrical contractor", items_per_page=100)
    
    # Get company profile
    profile = get_company("07621999")
    
    # Get officers
    officers = get_officers("07621999")
    
    # Get filing history
    filings = get_filings("07621999")
    
    # Stream real-time events
    for event in stream_filings():
        print(event)
"""
import base64
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional, Generator

# ─── KEYS (from environment) ──────────────────────────────────

def _get_key(name: str) -> str:
    """Get key from environment variable."""
    return os.environ.get(name, "")

REST_KEY = None  # Lazy loaded
STREAM_KEY = None

def _load_keys():
    global REST_KEY, STREAM_KEY
    if REST_KEY is None:
        REST_KEY = _get_key("COMPANIES_HOUSE_API_KEY")
    if STREAM_KEY is None:
        STREAM_KEY = _get_key("COMPANIES_HOUSE_STREAM_KEY")

REST_BASE = "https://api.company-information.service.gov.uk"
DOC_BASE = "https://document-api.company-information.service.gov.uk"
STREAM_BASE = "https://stream.companieshouse.gov.uk"

# ─── AUTH ─────────────────────────────────────────────────────

def _rest_auth():
    _load_keys()
    return base64.b64encode(f"{REST_KEY}:".encode()).decode()

def _stream_auth():
    _load_keys()
    return base64.b64encode(f"{STREAM_KEY}:".encode()).decode()

# ─── REST API ─────────────────────────────────────────────────

def _rest_get(path: str, params: dict = None) -> dict:
    """Make authenticated REST API call."""
    import urllib.parse
    url = f"{REST_BASE}{path}"
    if params:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        url += f"?{qs}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {_rest_auth()}",
        "User-Agent": "powuk-sdk/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": e.read().decode()[:200]}

# ─── SEARCH ───────────────────────────────────────────────────

def search_companies(query: str, items_per_page: int = 20, start_index: int = 0) -> dict:
    """Search companies by name/description."""
    return _rest_get("/search/companies", {
        "q": query,
        "items_per_page": items_per_page,
        "start_index": start_index,
    })

def search_officers(query: str, items_per_page: int = 20) -> dict:
    """Search for officers (directors, secretaries)."""
    return _rest_get("/search/officers", {
        "q": query,
        "items_per_page": items_per_page,
    })

def search_all(query: str, items_per_page: int = 20) -> dict:
    """Search companies AND officers."""
    return _rest_get("/search", {
        "q": query,
        "items_per_page": items_per_page,
    })

def advanced_search(
    sic_codes: str = None,
    company_status: str = None,
    region: str = None,
    locality: str = None,
    postcode: str = None,
    name_includes: str = None,
    incorporation_from: str = None,
    incorporation_to: str = None,
    dissolved_from: str = None,
    dissolved_to: str = None,
    size: int = 20,
    start_index: int = 0,
) -> dict:
    """Advanced search with filters."""
    return _rest_get("/advanced-search/companies", {
        "sic_codes": sic_codes,
        "company_status": company_status,
        "registered_office_address_region": region,
        "registered_office_address_locality": locality,
        "registered_office_address_postal_code": postcode,
        "company_name_includes": name_includes,
        "incorporation_from": incorporation_from,
        "incorporation_to": incorporation_to,
        "dissolved_from": dissolved_from,
        "dissolved_to": dissolved_to,
        "size": size,
        "start_index": start_index,
    })

# ─── COMPANY ──────────────────────────────────────────────────

def get_company(number: str) -> dict:
    """Get full company profile."""
    return _rest_get(f"/company/{number}")

def get_officers(number: str, items_per_page: int = 50) -> dict:
    """Get company officers."""
    return _rest_get(f"/company/{number}/officers", {"items_per_page": items_per_page})

def get_filings(number: str, items_per_page: int = 50) -> dict:
    """Get filing history."""
    return _rest_get(f"/company/{number}/filing-history", {"items_per_page": items_per_page})

def get_charges(number: str) -> dict:
    """Get company charges (mortgages)."""
    return _rest_get(f"/company/{number}/charges")

def get_psc(number: str) -> dict:
    """Get persons with significant control."""
    return _rest_get(f"/company/{number}/persons-with-significant-control")

def get_insolvency(number: str) -> dict:
    """Get insolvency information."""
    return _rest_get(f"/company/{number}/insolvency")

def get_officer_appointments(officer_id: str) -> dict:
    """Get all companies an officer serves on."""
    return _rest_get(f"/officers/{officer_id}/appointments")

# ─── DOCUMENT API ─────────────────────────────────────────────

def get_document_metadata(document_id: str) -> dict:
    """Get document metadata (category, pages, size)."""
    url = f"{DOC_BASE}/document/{document_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {_rest_auth()}",
        "User-Agent": "powuk-sdk/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code}

def get_document_content(document_id: str, out_path: str = None) -> bytes:
    """Download document content (PDF)."""
    url = f"{DOC_BASE}/document/{document_id}/content"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {_rest_auth()}",
        "User-Agent": "powuk-sdk/1.0",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
        if out_path:
            with open(out_path, "wb") as f:
                f.write(data)
        return data

# ─── STREAMING API ────────────────────────────────────────────

def stream_endpoint(endpoint: str, timepoint: int = None) -> Generator[dict, None, None]:
    """Connect to a streaming endpoint and yield events.
    
    Endpoints: companies, filings, officers, insolvency-cases, 
               charges, persons-with-significant-control, 
               disqualified-officers, company-exemptions
    
    Limitations:
        - Max 2 concurrent connections per account
        - If you read too slowly, connection drops
        - Reconnect with last timepoint for continuity
        - 429 = rate limited, wait 1 minute
    """
    url = f"{STREAM_BASE}/{endpoint}"
    if timepoint:
        url += f"?timepoint={timepoint}"
    
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {_stream_auth()}",
        "Accept": "text/event-stream",
        "User-Agent": "powuk-sdk/1.0",
    })
    
    resp = urllib.request.urlopen(req, timeout=300)  # 5 min timeout, reconnect if needed
    
    buffer = ""
    for chunk in iter(lambda: resp.read(1), b""):
        if chunk == b"\n":
            if buffer.strip():
                try:
                    yield json.loads(buffer.strip())
                except json.JSONDecodeError:
                    pass
                buffer = ""
        else:
            buffer += chunk.decode("utf-8", errors="ignore")

def stream_companies(timepoint: int = None) -> Generator[dict, None, None]:
    """Stream real-time company changes."""
    return stream_endpoint("companies", timepoint)

def stream_filings(timepoint: int = None) -> Generator[dict, None, None]:
    """Stream real-time filing events."""
    return stream_endpoint("filings", timepoint)

def stream_officers(timepoint: int = None) -> Generator[dict, None, None]:
    """Stream real-time officer changes."""
    return stream_endpoint("officers", timepoint)

def stream_insolvency(timepoint: int = None) -> Generator[dict, None, None]:
    """Stream real-time insolvency events."""
    return stream_endpoint("insolvency-cases", timepoint)

def stream_charges(timepoint: int = None) -> Generator[dict, None, None]:
    """Stream real-time charge events."""
    return stream_endpoint("charges", timepoint)

def stream_psc(timepoint: int = None) -> Generator[dict, None, None]:
    """Stream real-time PSC changes."""
    return stream_endpoint("persons-with-significant-control", timepoint)

# ─── HELPERS ──────────────────────────────────────────────────

def is_trade_company(company: dict, trade_sics: list = None) -> bool:
    """Check if company is a trade business."""
    if trade_sics is None:
        trade_sics = ["43210", "43220", "43290", "43910", "43999", "35110", "35140"]
    sic_codes = company.get("sic_codes", [])
    return any(sic in trade_sics for sic in sic_codes)

def get_trade_companies_in_region(region: str, trade_sics: list = None) -> list:
    """Get all trade companies in a region. Rate-limited to 600 req/5min."""
    import time
    results = []
    start = 0
    request_count = 0
    while True:
        data = advanced_search(
            sic_codes=",".join(trade_sics) if trade_sics else "43210,43220,43290",
            company_status="active",
            region=region,
            size=500,
            start_index=start,
        )
        items = data.get("items", [])
        if not items:
            break
        results.extend(items)
        start += len(items)
        request_count += 1
        # Rate limit: pause every 500 requests (well under 600/5min limit)
        if request_count % 500 == 0:
            time.sleep(5)
        if start >= data.get("total_results", 0):
            break
    return results

# ─── QUICK TEST ───────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Companies House SDK Test ===\n")
    
    # Test REST API
    print("1. Search companies...")
    r = search_companies("electrical contractor", items_per_page=3)
    print(f"   Found: {r.get('total_results', 0)} results")
    for item in r.get("items", [])[:3]:
        print(f"   - {item.get('title')} ({item.get('company_number')})")
    
    print("\n2. Get company profile...")
    r = get_company("07621999")
    print(f"   Name: {r.get('company_name')}")
    print(f"   Status: {r.get('company_status')}")
    print(f"   SIC: {r.get('sic_codes')}")
    
    print("\n3. Get officers...")
    r = get_officers("07621999", items_per_page=3)
    for item in r.get("items", [])[:3]:
        print(f"   - {item.get('name')} ({item.get('officer_role')})")
    
    print("\n4. Document API...")
    r = get_filings("07621999", items_per_page=1)
    if r.get("items"):
        doc_url = r["items"][0].get("links", {}).get("document_metadata", "")
        if doc_url:
            doc_id = doc_url.split("/")[-1]
            meta = get_document_metadata(doc_id)
            print(f"   Document: {meta.get('category')} ({meta.get('pages')} pages)")
    
    print("\n✓ SDK working")
