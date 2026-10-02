#!/usr/bin/env python3
"""Read independent numeric run summaries and print descriptive statistics."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path


def summarize(values: object) -> dict[str, int | float]:
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError("expected at least two independent numeric run values")
    if any(type(value) not in (int, float) for value in values):
        raise ValueError("run values must be numbers, not booleans or strings")
    try:
        if not all(math.isfinite(value) for value in values):
            raise ValueError("run values must be finite")
        mean = statistics.mean(values)
        sd = statistics.stdev(values)
        se = sd / math.sqrt(len(values))
        if not all(math.isfinite(value) for value in (mean, sd, se)):
            raise ValueError("summary is not finite at floating-point precision")
    except (OverflowError, statistics.StatisticsError) as exc:
        raise ValueError("values exceed supported numerical precision") from exc
    return {"n": len(values), "mean": mean, "sample_sd": sd, "standard_error": se}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="JSON array of independent run summaries")
    args = parser.parse_args()
    try:
        if not args.path.is_file():
            raise OSError("input is not a regular file")
        content = args.path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        parser.exit(2, f"cannot read input: {exc}\n")
    try:
        result = summarize(json.loads(content))
    except (ValueError, RecursionError) as exc:
        parser.exit(1, f"invalid run summaries: {exc}\n")
    print(json.dumps(result, allow_nan=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
