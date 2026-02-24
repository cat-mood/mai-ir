#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Zipf rank-frequency plot from CSV."
    )
    parser.add_argument(
        "--input",
        default="search_engine/zipf_stats.csv",
        help="Path to zipf_stats.csv (default: search_engine/zipf_stats.csv)",
    )
    parser.add_argument(
        "--output",
        default="zipf_plot.png",
        help="Output image path (default: zipf_plot.png)",
    )
    parser.add_argument(
        "--max-rank",
        type=int,
        default=0,
        help="Use only first N ranks (0 means all).",
    )
    parser.add_argument(
        "--hide-theory",
        action="store_true",
        help="Do not draw theoretical Zipf curve f(r)=C/r.",
    )
    return parser.parse_args()


def load_zipf_points(csv_path: Path, max_rank: int = 0) -> tuple[list[int], list[int]]:
    ranks: list[int] = []
    freqs: list[int] = []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rank = int(row["rank"])
            freq = int(row["frequency"])
            if rank <= 0 or freq <= 0:
                continue
            if max_rank > 0 and rank > max_rank:
                break
            ranks.append(rank)
            freqs.append(freq)

    if not ranks:
        raise ValueError("No valid points were loaded from CSV.")

    return ranks, freqs


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    ranks, freqs = load_zipf_points(input_path, args.max_rank)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.loglog(ranks, freqs, linewidth=1.5, label="Corpus frequencies")

    if not args.hide_theory:
        c = freqs[0]
        zipf = [c / r for r in ranks]
        ax.loglog(ranks, zipf, linewidth=1.5, label="Zipf (C/r)")

    ax.set_title("Zipf law: rank-frequency")
    ax.set_xlabel("Rank (log)")
    ax.set_ylabel("Frequency (log)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved plot: {output_path}")


if __name__ == "__main__":
    main()
