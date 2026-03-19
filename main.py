import os
import re
import csv
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

# =========================
# CONFIG
# =========================

API_URL = "https://api.trove.nla.gov.au/v3/result"
TROVE_API_KEY = "Trove_API_KEY"

OUT_DIR = "data"
OUT_JSONL = os.path.join(OUT_DIR, "trove_armenian_duduk.jsonl")
OUT_CSV = os.path.join(OUT_DIR, "trove_armenian_duduk.csv")

CATEGORY = "music"
QUERY = "armenian duduk"

MAX_RECORDS = None

PAGE_SIZE = 100
SLEEP_SECONDS = 0.2
INCLUDE = ["workversions", "holdings", "links"]

# =========================
# UTILITIES
# =========================

def norm(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, list):
        vals = [norm(v) for v in value]
        vals = [v for v in vals if v]
        return ", ".join(vals) if vals else None

    if isinstance(value, dict):
        for key in ["value", "text", "#text", "name", "title"]:
            if key in value:
                return norm(value[key])
        return None

    s = str(value)
    s = re.sub(r"[\[\]\{\}']", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s or None


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def to_list(x: Any) -> List[Any]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def get_with_retries(
    url: str,
    params: List[Tuple[str, str]],
    timeout: int = 120,
    max_tries: int = 6,
) -> requests.Response:
    last_err = None
    for attempt in range(1, max_tries + 1):
        try:
            return requests.get(url, params=params, timeout=timeout)
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
        ) as e:
            last_err = e
            sleep_s = min(60, 2 ** attempt)
            print(f"[retry {attempt}/{max_tries}] timeout/network error, sleeping {sleep_s}s")
            time.sleep(sleep_s)
    raise last_err  # type: ignore


def get_page(cursor: str) -> Dict[str, Any]:
    params: List[Tuple[str, str]] = [
        ("key", TROVE_API_KEY),
        ("encoding", "json"),
        ("category", CATEGORY),
        ("q", QUERY),
        ("reclevel", "full"),
        ("n", str(PAGE_SIZE)),
        ("s", cursor),
    ]

    for inc in INCLUDE:
        params.append(("include", inc))

    r = get_with_retries(API_URL, params=params)
    r.raise_for_status()
    return r.json()

# =========================
# PARSING
# =========================

def find_records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    cats = payload.get("category", [])
    if not cats:
        return []
    recs = cats[0].get("records", {})
    works = recs.get("work", [])
    return works if isinstance(works, list) else []


def find_next_cursor(payload: Dict[str, Any]) -> Optional[str]:
    cats = payload.get("category", [])
    if not cats:
        return None
    recs = cats[0].get("records", {})
    nxt = recs.get("nextStart")
    return nxt if isinstance(nxt, str) and nxt.strip() else None


def total_results(payload: Dict[str, Any]) -> Optional[int]:
    cats = payload.get("category", [])
    if not cats:
        return None
    recs = cats[0].get("records", {})
    total = recs.get("total")
    return total if isinstance(total, int) else None

# =========================
# EXTRACTION
# =========================

def extract_work(work: Dict[str, Any]) -> Dict[str, Any]:
    title = norm(work.get("title"))
    date = norm(work.get("issued")) or norm(work.get("date"))

    contributors = to_list(work.get("contributor"))
    creator = ", ".join([norm(c) for c in contributors if norm(c)]) or None

    description = norm(work.get("abstract"))
    trove_url = norm(work.get("troveUrl"))

    best_url = trove_url
    for ident in to_list(work.get("identifier")):
        if isinstance(ident, str) and ident.startswith("http"):
            best_url = ident
            break
        if isinstance(ident, dict):
            val = ident.get("value") or ident.get("text") or ident.get("#text")
            if isinstance(val, str) and val.startswith("http"):
                best_url = val
                break

    return {
        "title": title,
        "date_or_period": date,
        "author_or_creator": creator,
        "description_or_abstract": description,
        "url_to_original_object": best_url,
        "trove_id": norm(work.get("id") or work.get("@id")),
        "trove_url": trove_url,
    }

# =========================
# SAVE
# =========================

def save_jsonl(rows: List[Dict[str, Any]]) -> None:
    ensure_dir(OUT_DIR)
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_csv(rows: List[Dict[str, Any]]) -> None:
    ensure_dir(OUT_DIR)
    columns = [
        "title",
        "date_or_period",
        "author_or_creator",
        "description_or_abstract",
        "url_to_original_object",
        "trove_id",
        "trove_url",
    ]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c) for c in columns})

# =========================
# MAIN
# =========================

def main() -> None:
    if not TROVE_API_KEY:
        raise SystemExit(
            "Missing TROVE_API_KEY.\n"
            "PyCharm -> Run -> Edit Configurations -> Environment variables\n"
            "Add TROVE_API_KEY=your_key_here"
        )

    ensure_dir(OUT_DIR)

    cursor = "*"
    seen_ids = set()
    seen_cursors = {cursor}
    rows: List[Dict[str, Any]] = []
    page_num = 0

    print("Query:", QUERY)
    print("Category:", CATEGORY)
    print("Max records:", MAX_RECORDS)
    print()

    while True:
        if MAX_RECORDS is not None and len(rows) >= MAX_RECORDS:
            break

        payload = get_page(cursor)
        page_num += 1

        if page_num == 1:
            print("Total results reported by Trove:", total_results(payload))

        records = find_records(payload)
        if not records:
            break

        for rec in records:
            if MAX_RECORDS is not None and len(rows) >= MAX_RECORDS:
                break

            row = extract_work(rec)

            tid = row.get("trove_id")
            if tid and tid in seen_ids:
                continue
            if tid:
                seen_ids.add(tid)

            rows.append(row)

        print(f"Fetched page {page_num}, saved rows so far: {len(rows)}")

        next_cursor = find_next_cursor(payload)
        if not next_cursor or next_cursor == cursor or next_cursor in seen_cursors:
            break

        seen_cursors.add(next_cursor)
        cursor = next_cursor
        time.sleep(SLEEP_SECONDS)

    save_jsonl(rows)
    save_csv(rows)

    print("\nDONE")
    print("Rows:", len(rows))
    print("JSONL:", OUT_JSONL)
    print("CSV:", OUT_CSV)


if __name__ == "__main__":
    main()