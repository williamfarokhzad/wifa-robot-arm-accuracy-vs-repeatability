"""Analyze planar robot endpoint samples in millimetres, without hardware I/O."""

import argparse
import csv
from dataclasses import dataclass
import math
from pathlib import Path
from statistics import fmean

HEADER = ["x_mm", "y_mm"]
Point = tuple[float, float]


@dataclass(frozen=True)
class Result:
    center: Point
    offset: Point
    center_error_mm: float
    rms_spread_mm: float
    max_target_error_mm: float


def summarize(target: Point, readings: list[Point]) -> Result:
    if len(readings) < 2:
        raise ValueError("provide at least two readings")
    for point in (target, *readings):
        if len(point) != 2 or not all(math.isfinite(v) and abs(v) <= 1e9 for v in point):
            raise ValueError("use two finite millimetre coordinates within ±1e9")
    cx, cy = (fmean(axis) for axis in zip(*readings))
    offset = (cx - target[0], cy - target[1])
    distances = [math.dist((cx, cy), point) for point in readings]
    return Result(
        (cx, cy), offset, math.hypot(*offset),
        math.sqrt(fmean(d * d for d in distances)),
        max(math.dist(target, point) for point in readings),
    )


def read_points(path: Path) -> list[Point]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.reader(handle, strict=True)
        if next(rows, None) != HEADER:
            raise ValueError("CSV header must be x_mm,y_mm")
        result = []
        for row in rows:
            try:
                if len(row) != 2:
                    raise ValueError()
                result.append((float(row[0]), float(row[1])))
            except ValueError as exc:
                raise ValueError(f"CSV line {rows.line_num}: expected two numeric fields") from exc
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--target", nargs=2, type=float, required=True, metavar=("X_MM", "Y_MM"))
    args = parser.parse_args()
    try:
        result = summarize(tuple(args.target), read_points(args.csv_file))
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    print(f"Mean endpoint: ({result.center[0]:.3f}, {result.center[1]:.3f}) mm")
    print(f"Mean offset X/Y: ({result.offset[0]:+.3f}, {result.offset[1]:+.3f}) mm")
    print(f"Mean endpoint error: {result.center_error_mm:.3f} mm")
    print(f"RMS spread around mean: {result.rms_spread_mm:.3f} mm")
    print(f"Largest observed target error: {result.max_target_error_mm:.3f} mm")


if __name__ == "__main__":
    main()
