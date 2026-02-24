#!/usr/bin/env python3
import json
import subprocess
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse

from metrics import calculate_all_metrics


def load_doc_id_to_url(index_dir: str) -> dict:
    mapping = {}
    documents_path = Path(index_dir) / "documents.txt"
    if not documents_path.exists():
        return mapping

    with documents_path.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t", 2)
            if len(parts) < 2:
                continue
            try:
                doc_id = int(parts[0])
            except ValueError:
                continue
            mapping[doc_id] = parts[1]

    return mapping


def run_search(query: str, search_cli: str, index_dir: str) -> list:
    try:
        process = subprocess.Popen(
            [search_cli, index_dir],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = process.communicate(input=query + "\n", timeout=30)
        if process.returncode != 0:
            print(
                f"Search CLI failed for query '{query}' (code {process.returncode}): {stderr}",
                file=sys.stderr,
            )
            return []

        doc_ids = []
        lines = stdout.strip().split("\n")

        parsing_results = False
        for line in lines:
            if line.startswith("Found"):
                parsing_results = True
                continue

            if parsing_results and "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 1:
                    try:
                        doc_id = int(parts[0].strip())
                        doc_ids.append(doc_id)
                    except ValueError:
                        continue

        return doc_ids

    except Exception as e:
        print(f"Error running search for query '{query}': {e}", file=sys.stderr)
        return []


def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def evaluate_search_engine(
    ground_truth_file: str,
    search_cli: str,
    index_dir: str,
    source_domain: str = "",
    strict_url_qrels: bool = True,
):
    with open(ground_truth_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    queries = ground_truth["queries"]
    doc_id_to_url = load_doc_id_to_url(index_dir)
    all_index_urls = set(doc_id_to_url.values())

    print("=== Search Engine Evaluation ===\n")
    print(f"Total queries: {len(queries)}\n")

    query_coverages = []
    total_relevant_items = 0
    total_covered_items = 0
    url_qrels_queries = 0

    all_metrics = {
        "P@5": [],
        "P@10": [],
        "P@20": [],
        "DCG@5": [],
        "DCG@10": [],
        "DCG@20": [],
        "NDCG@5": [],
        "NDCG@10": [],
        "NDCG@20": [],
        "ERR@5": [],
        "ERR@10": [],
        "ERR@20": [],
    }

    for query_data in queries:
        query_id = query_data["id"]
        query = query_data["query"]
        use_url_ground_truth = "relevant_urls" in query_data
        if strict_url_qrels and not use_url_ground_truth:
            print(f'Query {query_id}: "{query}"')
            print("  Skipped: strict URL qrels mode requires `relevant_urls`.\n")
            continue

        if use_url_ground_truth:
            url_qrels_queries += 1
            relevant_docs = {k: int(v) for k, v in query_data["relevant_urls"].items()}
            if source_domain:
                relevant_docs = {
                    url: grade
                    for url, grade in relevant_docs.items()
                    if extract_domain(url) == source_domain
                }
            relevant_count = len(relevant_docs)
            covered_count = sum(1 for url in relevant_docs if url in all_index_urls)
        else:
            relevant_docs = {int(k): int(v) for k, v in query_data["relevant_docs"].items()}
            relevant_count = len(relevant_docs)
            covered_count = sum(1 for doc_id in relevant_docs if doc_id in doc_id_to_url)

        coverage = (covered_count / relevant_count) if relevant_count else 0.0
        query_coverages.append(coverage)
        total_relevant_items += relevant_count
        total_covered_items += covered_count

        print(f'Query {query_id}: "{query}"')
        print(f"  Qrels coverage in index: {covered_count}/{relevant_count} ({coverage:.2%})")

        retrieved = run_search(query, search_cli, index_dir)
        if use_url_ground_truth:
            retrieved = [doc_id_to_url[doc_id] for doc_id in retrieved if doc_id in doc_id_to_url]
            if source_domain:
                retrieved = [url for url in retrieved if extract_domain(url) == source_domain]

        if not retrieved:
            print("  No results returned\n")
            continue

        print(f"  Retrieved {len(retrieved)} documents")

        metrics = calculate_all_metrics(retrieved, relevant_docs)

        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.4f}")
            all_metrics[metric_name].append(value)

        print()

    print("\n=== Average Metrics Across All Queries ===\n")

    for metric_name, values in all_metrics.items():
        if values:
            avg = sum(values) / len(values)
            print(f"{metric_name}: {avg:.4f}")

    print("\n=== Qrels Coverage Summary ===\n")
    avg_coverage = (sum(query_coverages) / len(query_coverages)) if query_coverages else 0.0
    global_coverage = (total_covered_items / total_relevant_items) if total_relevant_items else 0.0
    print(f"Queries with URL qrels: {url_qrels_queries}/{len(queries)}")
    if source_domain:
        print(f"Source-domain filter: {source_domain}")
    print(f"Average per-query qrels coverage: {avg_coverage:.2%}")
    print(f"Global qrels coverage: {total_covered_items}/{total_relevant_items} ({global_coverage:.2%})")
    if avg_coverage < 0.5:
        print("WARNING: Low qrels coverage can make metric values unreliable.")

    print("\n=== Evaluation Complete ===")


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Evaluate search quality metrics.")
    parser.add_argument(
        "ground_truth_file",
        nargs="?",
        default=str(script_dir / "queries_ground_truth_urls.json"),
        help="Path to qrels JSON file (with relevant_urls).",
    )
    parser.add_argument(
        "search_cli",
        nargs="?",
        default=str(script_dir.parent / "search_engine" / "build" / "search_cli"),
        help="Path to search_cli executable.",
    )
    parser.add_argument(
        "index_dir",
        nargs="?",
        default=str(script_dir.parent / "search_engine" / "index"),
        help="Path to index directory.",
    )
    parser.add_argument(
        "--source-domain",
        default="",
        help="Evaluate only URLs from a specific domain (e.g. fallout.bethesda.net).",
    )
    parser.add_argument(
        "--allow-doc-id-qrels",
        action="store_true",
        help="Allow fallback to old `relevant_docs` doc_id qrels.",
    )
    args = parser.parse_args()

    evaluate_search_engine(
        str(Path(args.ground_truth_file).expanduser()),
        str(Path(args.search_cli).expanduser()),
        str(Path(args.index_dir).expanduser()),
        source_domain=args.source_domain.strip().lower(),
        strict_url_qrels=not args.allow_doc_id_qrels,
    )
