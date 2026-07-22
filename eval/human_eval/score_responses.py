"""Aggregate Explanation Satisfaction Scale responses after real data collection."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ESS_ITEMS = tuple(f"ESS-{idx}" for idx in range(1, 10))
GENERATED_DIR = Path(__file__).resolve().parent / "generated"


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_responses(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        for row in _read_csv(path):
            missing = [item for item in ESS_ITEMS if not str(row.get(item, "")).strip()]
            if missing:
                raise ValueError(f"{path}: missing ratings for {row.get('stimulus_id')} ({missing})")
            parsed = dict(row)
            for item in ESS_ITEMS:
                parsed[item] = float(parsed[item])
            parsed["ess_mean"] = _mean([parsed[item] for item in ESS_ITEMS])
            rows.append(parsed)
    if not rows:
        raise ValueError("No response rows loaded.")
    return rows


def join_with_key(responses: list[dict], key_path: Path) -> list[dict]:
    key_rows = {row["stimulus_id"]: row for row in _read_csv(key_path)}
    joined: list[dict] = []
    for row in responses:
        sid = row["stimulus_id"]
        if sid not in key_rows:
            raise KeyError(f"Stimulus {sid} missing from randomization key.")
        joined.append({**row, **key_rows[sid]})
    return joined


def summarize(joined: list[dict]) -> dict:
    by_system: dict[str, list[float]] = defaultdict(list)
    by_category: dict[str, list[float]] = defaultdict(list)
    by_item: dict[str, list[float]] = defaultdict(list)
    for row in joined:
        by_system[row["system_actual"]].append(row["ess_mean"])
        by_category[row["category"]].append(row["ess_mean"])
        for item in ESS_ITEMS:
            by_item[item].append(float(row[item]))

    return {
        "participants": sorted({row["participant_id"] for row in joined}),
        "response_count": len(joined),
        "ess_mean_overall": round(_mean([row["ess_mean"] for row in joined]), 3),
        "ess_mean_by_system": {
            system: round(_mean(values), 3) for system, values in sorted(by_system.items())
        },
        "ess_mean_by_category": {
            category: round(_mean(values), 3)
            for category, values in sorted(by_category.items())
        },
        "ess_mean_by_item": {item: round(_mean(values), 3) for item, values in by_item.items()},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "responses",
        nargs="+",
        type=Path,
        help="One or more completed response CSV files.",
    )
    parser.add_argument(
        "--key",
        type=Path,
        default=GENERATED_DIR / "randomization_key.csv",
        help="Randomization key produced by build_stimuli.py.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=GENERATED_DIR / "ess_summary.json",
        help="Where to write aggregated ESS summary JSON.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    responses = load_responses(args.responses)
    joined = join_with_key(responses, args.key)
    summary = summarize(joined)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote summary to {args.out}")


if __name__ == "__main__":
    main()
