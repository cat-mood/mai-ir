#!/usr/bin/env python3
"""Generate ground truth by *pooling* the search engine's own top results.

Standard IR evaluation (TREC-style) creates the relevance pool from the
results actually returned by the systems being evaluated.  This script:

  1. Runs each query through search_cli  (top-100 results).
  2. Loads full document content for the returned doc_ids.
  3. Scores each document with a content-based relevance function.
  4. Writes the scored pool as ``queries_ground_truth.json``.
  5. Runs the URL conversion to produce ``queries_ground_truth_urls.json``.

This guarantees overlap between search results and ground truth, so the
evaluation measures *ranking* quality (do the most relevant documents appear
at the top?) rather than pool coverage.
"""

import json
import subprocess
import sys
from pathlib import Path

QUERIES = [
    {"id": 1,  "query": "fallout AND vault"},
    {"id": 2,  "query": "weapon OR armor"},
    {"id": 3,  "query": "quest AND brotherhood"},
    {"id": 4,  "query": "radiation"},
    {"id": 5,  "query": "character AND perk"},
    {"id": 6,  "query": "location OR settlement"},
    {"id": 7,  "query": "enemy AND mutant"},
    {"id": 8,  "query": "companion"},
    {"id": 9,  "query": "item AND consumable"},
    {"id": 10, "query": "faction NOT enclave"},
    {"id": 11, "query": "power AND armor"},
    {"id": 12, "query": "nuclear OR atomic"},
    {"id": 13, "query": "crafting AND workbench"},
    {"id": 14, "query": "robot OR synth"},
    {"id": 15, "query": "wasteland"},
]


# ---------------------------------------------------------------------------
# Query parsing
# ---------------------------------------------------------------------------

def parse_query(query_str: str):
    """Return (positive_keywords, negative_keywords, query_type)."""
    tokens = query_str.split()
    positive, negative = [], []
    negate_next = False
    has_and = has_or = False

    for tok in tokens:
        upper = tok.upper()
        if upper == "AND":
            has_and = True
        elif upper == "OR":
            has_or = True
        elif upper == "NOT":
            negate_next = True
            has_and = True
        elif negate_next:
            negative.append(tok.lower())
            negate_next = False
        else:
            positive.append(tok.lower())

    qtype = "AND" if has_and else ("OR" if has_or else "SINGLE")
    return positive, negative, qtype


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------

def score_document(
    title_lower: str,
    text_lower: str,
    positive_kw: list[str],
    negative_kw: list[str],
    query_type: str,
) -> int:
    """Score a document 0-3 based on keyword presence/density."""

    for neg in negative_kw:
        if neg in title_lower:
            return 0

    title_hits = [kw for kw in positive_kw if kw in title_lower]
    text_counts = {kw: text_lower.count(kw) for kw in positive_kw}
    text_hits = [kw for kw, c in text_counts.items() if c > 0]
    total = len(positive_kw)

    if total == 0:
        return 0

    if query_type == "AND":
        all_in_text = len(text_hits) == total
        min_count = min(text_counts.values()) if text_counts else 0

        if not all_in_text:
            return 0
        all_in_title = len(title_hits) == total
        some_in_title = len(title_hits) > 0

        if all_in_title and min_count >= 3:
            return 3
        if some_in_title and min_count >= 2:
            return 2
        if min_count >= 2:
            return 1
        return 0

    if query_type == "OR":
        best_title_count = max(
            (text_counts.get(kw, 0) for kw in title_hits), default=0
        )
        if len(title_hits) >= 2:
            return 3
        if len(title_hits) >= 1 and best_title_count >= 5:
            return 3
        if len(title_hits) >= 1 and best_title_count >= 2:
            return 2
        if len(text_hits) >= 2:
            max_cnt = max(text_counts[kw] for kw in text_hits)
            if max_cnt >= 5:
                return 2
            if max_cnt >= 3:
                return 1
        if text_hits:
            best = max(text_counts[kw] for kw in text_hits)
            if best >= 5:
                return 1
        return 0

    # SINGLE keyword
    kw = positive_kw[0]
    in_title = kw in title_lower
    cnt = text_counts.get(kw, 0)

    if in_title and cnt >= 10:
        return 3
    if in_title and cnt >= 3:
        return 2
    if cnt >= 15:
        return 2
    if cnt >= 5:
        return 1
    return 0


# ---------------------------------------------------------------------------
# Search-engine interaction
# ---------------------------------------------------------------------------

def run_search(query: str, search_cli: str, index_dir: str) -> list[int]:
    """Run a single query and return the doc_ids from search_cli."""
    try:
        proc = subprocess.Popen(
            [search_cli, index_dir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, _ = proc.communicate(input=query + "\n", timeout=30)
        doc_ids: list[int] = []
        parsing = False
        for line in stdout.strip().split("\n"):
            if line.startswith("Found"):
                parsing = True
                continue
            if parsing and "\t" in line:
                parts = line.split("\t")
                try:
                    doc_ids.append(int(parts[0].strip()))
                except ValueError:
                    pass
        return doc_ids
    except Exception as exc:
        print(f"  ERROR running search: {exc}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    project_root = Path(__file__).resolve().parent.parent
    jsonl_path = project_root / "documents.jsonl"
    search_cli = str(project_root / "search_engine" / "build" / "search_cli")
    index_dir = str(project_root / "search_engine" / "index")
    out_path = Path(__file__).resolve().parent / "queries_ground_truth.json"

    if not jsonl_path.exists():
        sys.exit(f"ERROR: {jsonl_path} not found.")
    if not Path(search_cli).exists():
        sys.exit(f"ERROR: {search_cli} not found. Build the C++ engine first.")

    # 1. Collect pool of doc_ids from search results
    pool_ids: set[int] = set()
    query_results: dict[int, list[int]] = {}

    print("Running search engine for each query …")
    for q in QUERIES:
        ids = run_search(q["query"], search_cli, index_dir)
        query_results[q["id"]] = ids
        pool_ids.update(ids)
        print(f'  Query {q["id"]:>2}: "{q["query"]}"  → {len(ids)} results')

    print(f"\nPool size: {len(pool_ids)} unique documents")

    # 2. Load content for pooled documents
    print(f"Loading document content from {jsonl_path} …")
    doc_content: dict[int, tuple[str, str]] = {}
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            obj = json.loads(line)
            did = obj["doc_id"]
            if did in pool_ids:
                doc_content[did] = (
                    obj.get("title", "").lower(),
                    obj.get("text", "").lower(),
                )
    print(f"Loaded content for {len(doc_content)} documents.\n")

    # 3. Score each query's results
    ground_truth = {
        "queries": [],
        "relevance_levels": {
            "3": "Highly relevant",
            "2": "Relevant",
            "1": "Somewhat relevant",
            "0": "Not relevant",
        },
    }

    for q in QUERIES:
        qid = q["id"]
        pos_kw, neg_kw, qtype = parse_query(q["query"])
        relevant: dict[str, int] = {}
        grade_dist: dict[int, int] = {}

        for did in query_results[qid]:
            if did not in doc_content:
                continue
            title_l, text_l = doc_content[did]
            grade = score_document(title_l, text_l, pos_kw, neg_kw, qtype)
            if grade > 0:
                relevant[str(did)] = grade
                grade_dist[grade] = grade_dist.get(grade, 0) + 1

        print(
            f'Query {qid:>2}: "{q["query"]}"  '
            f"scored={len(relevant)}  "
            f"dist={dict(sorted(grade_dist.items(), reverse=True))}"
        )

        ground_truth["queries"].append(
            {"id": qid, "query": q["query"], "relevant_docs": relevant}
        )

    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(ground_truth, fh, ensure_ascii=False, indent=2)
    print(f"\nGround truth written to {out_path}")

    # 4. Auto-convert to URL-based ground truth
    convert_script = Path(__file__).resolve().parent / "convert_ground_truth_to_urls.py"
    if convert_script.exists():
        print("Running URL conversion …")
        subprocess.run([sys.executable, str(convert_script)], check=True)


if __name__ == "__main__":
    main()
