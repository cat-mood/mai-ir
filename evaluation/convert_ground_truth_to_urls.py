#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def load_doc_id_to_url(documents_txt_path: Path) -> dict:
    mapping = {}
    with documents_txt_path.open("r", encoding="utf-8") as f:
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


def convert_ground_truth(input_path: Path, documents_txt_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    doc_id_to_url = load_doc_id_to_url(documents_txt_path)
    queries = data.get("queries", [])

    for query in queries:
        relevant_docs = query.get("relevant_docs", {})
        relevant_urls = {}

        for doc_id_str, grade in relevant_docs.items():
            try:
                doc_id = int(doc_id_str)
            except ValueError:
                continue

            url = doc_id_to_url.get(doc_id)
            if url:
                relevant_urls[url] = int(grade)

        query["relevant_urls"] = relevant_urls

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Converted ground truth saved to: {output_path}")


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else script_dir / "queries_ground_truth.json"
    documents_txt_path = (
        Path(sys.argv[2]) if len(sys.argv) > 2
        else script_dir.parent / "search_engine" / "index" / "documents.txt"
    )
    output_path = (
        Path(sys.argv[3]) if len(sys.argv) > 3
        else script_dir / "queries_ground_truth_urls.json"
    )

    convert_ground_truth(input_path, documents_txt_path, output_path)
