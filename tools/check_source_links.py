"""Check source URLs in chatbot_faq.json and disease_info.json.

Requests every source URL (HEAD, then GET on failure, 15 s timeout, follow redirects, browser-like User-Agent)
and prints a table: id, URL, status code or error, final URL.
Supports updating url_status ("ok", "unverified", "dead") and url_checked_on date in JSON files.
"""

import argparse
from datetime import date
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 15.0


def check_url(url: str, timeout: float = TIMEOUT) -> tuple[str, str, str]:
    """Test URL using HEAD, falling back to GET.
    
    Returns (status_or_error, final_url, url_status)
    where url_status is one of: "ok", "unverified", "dead".
    """
    if not url:
        return "NO_URL", "", "dead"

    headers = {"User-Agent": USER_AGENT}

    # 1. Try HEAD first
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            if 200 <= status < 400:
                return str(status), resp.geturl(), "ok"
            elif status in (404, 410):
                return str(status), resp.geturl(), "dead"
            return str(status), resp.geturl(), "unverified"
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            return f"HTTP {exc.code}", url, "dead"
        # Some servers return 403 or 405 for HEAD; retry with GET
    except Exception:
        pass

    # 2. Try GET if HEAD was not 200/redirected
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            if 200 <= status < 400:
                return str(status), resp.geturl(), "ok"
            elif status in (404, 410):
                return str(status), resp.geturl(), "dead"
            return str(status), resp.geturl(), "unverified"
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            return f"HTTP {exc.code}", url, "dead"
        return f"HTTP {exc.code}", url, "unverified"
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if "getaddrinfo failed" in reason.lower() or "name or service not known" in reason.lower() or "11001" in reason:
            return "DNS_ERROR (NXDOMAIN)", url, "unverified"
        if "timed out" in reason.lower() or "timeout" in reason.lower():
            return "TIMEOUT", url, "unverified"
        if "certificate" in reason.lower() or "ssl" in reason.lower():
            return f"SSL_ERROR: {reason[:40]}", url, "unverified"
        return f"URL_ERROR: {reason[:50]}", url, "unverified"
    except TimeoutError:
        return "TIMEOUT", url, "unverified"
    except Exception as exc:
        return f"ERROR: {str(exc)[:50]}", url, "unverified"


def collect_sources(workspace_root: Path) -> dict[str, dict]:
    sources: dict[str, dict] = {}
    faq_path = workspace_root / "backend" / "data" / "chatbot_faq.json"
    disease_path = workspace_root / "backend" / "data" / "disease_info.json"

    if faq_path.exists():
        with open(faq_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for sid, sinfo in data.get("sources", {}).items():
                sources[sid] = sinfo

    if disease_path.exists():
        with open(disease_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for sid, sinfo in data.get("sources", {}).items():
                if sid not in sources:
                    sources[sid] = sinfo

    return sources


def run_checks(workspace_root: Path = None, apply_updates: bool = False):
    if workspace_root is None:
        workspace_root = Path(__file__).resolve().parent.parent

    sources = collect_sources(workspace_root)
    results = []
    checked_date = date.today().isoformat()

    print(f"Checking {len(sources)} sources from chatbot_faq.json and disease_info.json...\n")
    for sid in sorted(sources.keys()):
        sinfo = sources[sid]
        url = sinfo.get("url", "")
        status_or_err, final_url, url_status = check_url(url)
        results.append({
            "id": sid,
            "url": url,
            "status": status_or_err,
            "final_url": final_url,
            "url_status": url_status,
            "title": sinfo.get("title", ""),
            "checked_on": checked_date,
        })

    # Print markdown table
    print("| ID | URL | Status / Error | Final URL | URL Status |")
    print("|---|---|---|---|---|")
    for r in results:
        status_display = r["status"]
        final_display = r["final_url"] if r["final_url"] != r["url"] else "Same"
        print(f"| {r['id']} | {r['url']} | {status_display} | {final_display} | {r['url_status']} |")

    if apply_updates:
        status_map = {r["id"]: (r["url_status"], r["checked_on"]) for r in results}
        for file_rel in ["backend/data/chatbot_faq.json", "backend/data/disease_info.json"]:
            fpath = workspace_root / file_rel
            if fpath.exists():
                with open(fpath, "r", encoding="utf-8") as f:
                    content = json.load(f)
                if "sources" in content:
                    for sid, sdata in content["sources"].items():
                        if sid in status_map:
                            sdata["url_status"] = status_map[sid][0]
                            sdata["url_checked_on"] = status_map[sid][1]
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                print(f"Updated {file_rel} with url_status and url_checked_on.")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check source URLs")
    parser.add_argument("--apply", action="store_true", help="Apply url_status and url_checked_on to JSON files")
    args = parser.parse_args()
    run_checks(apply_updates=args.apply)
