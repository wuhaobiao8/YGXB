#!/usr/bin/env python3
"""Convert a LAS/LAZ point cloud into a lightweight JSON demo for the web site.

The output format is intentionally simple so future editors can replace the
demo dataset without touching frontend code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import laspy
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a LAS/LAZ point cloud into a lightweight demo JSON."
    )
    parser.add_argument("--input", required=True, help="Path to the source LAS/LAZ file.")
    parser.add_argument("--output", required=True, help="Path to the output JSON file.")
    parser.add_argument(
        "--max-points",
        type=int,
        default=18000,
        help="Maximum number of points to keep in the demo output.",
    )
    parser.add_argument(
        "--crop-size",
        type=float,
        default=90.0,
        help="Centered square crop size in meters. Use 0 to disable cropping.",
    )
    parser.add_argument(
        "--vertical-scale",
        type=float,
        default=1.6,
        help="Vertical exaggeration applied after normalizing elevation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for reproducible sampling.",
    )
    return parser.parse_args()


def normalize_colors(values: np.ndarray) -> np.ndarray:
    vmax = int(values.max()) if values.size else 255
    if vmax <= 255:
      return values.astype(np.uint8)
    return np.clip(values / 256, 0, 255).astype(np.uint8)


def main() -> None:
    args = parse_args()
    source_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    las = laspy.read(source_path)
    x = np.asarray(las.x, dtype=np.float64)
    y = np.asarray(las.y, dtype=np.float64)
    z = np.asarray(las.z, dtype=np.float64)
    classes = (
        np.asarray(las.classification, dtype=np.uint8)
        if hasattr(las, "classification")
        else np.zeros_like(x, dtype=np.uint8)
    )

    if all(hasattr(las, channel) for channel in ("red", "green", "blue")):
        red = normalize_colors(np.asarray(las.red))
        green = normalize_colors(np.asarray(las.green))
        blue = normalize_colors(np.asarray(las.blue))
    else:
        red = np.full_like(classes, 120, dtype=np.uint8)
        green = np.full_like(classes, 170, dtype=np.uint8)
        blue = np.full_like(classes, 220, dtype=np.uint8)

    mask = np.ones_like(x, dtype=bool)
    if args.crop_size and args.crop_size > 0:
        cx = float((x.min() + x.max()) / 2)
        cy = float((y.min() + y.max()) / 2)
        half = args.crop_size / 2
        mask = (
            (x >= cx - half)
            & (x <= cx + half)
            & (y >= cy - half)
            & (y <= cy + half)
        )

    idx = np.nonzero(mask)[0]
    if idx.size == 0:
        raise SystemExit("No points left after cropping; increase --crop-size.")

    rng = np.random.default_rng(args.seed)
    if idx.size > args.max_points:
        ground_idx = idx[classes[idx] == 2]
        other_idx = idx[classes[idx] != 2]

        keep_ground = min(len(ground_idx), max(args.max_points // 3, 1))
        keep_other = args.max_points - keep_ground

        chosen = []
        if keep_ground:
            chosen.append(rng.choice(ground_idx, size=keep_ground, replace=False))
        if keep_other and len(other_idx):
            chosen.append(
                rng.choice(other_idx, size=min(len(other_idx), keep_other), replace=False)
            )

        sampled = np.concatenate(chosen) if chosen else rng.choice(idx, size=args.max_points, replace=False)
        if sampled.size < args.max_points:
            remain = np.setdiff1d(idx, sampled, assume_unique=False)
            if remain.size:
                extra = rng.choice(
                    remain,
                    size=min(args.max_points - sampled.size, remain.size),
                    replace=False,
                )
                sampled = np.concatenate([sampled, extra])
        idx = np.sort(sampled[: args.max_points])

    sx = x[idx]
    sy = y[idx]
    sz = z[idx]
    sr = red[idx]
    sg = green[idx]
    sb = blue[idx]
    sc = classes[idx]

    center_x = float((sx.min() + sx.max()) / 2)
    center_y = float((sy.min() + sy.max()) / 2)
    min_z = float(sz.min())

    local_x = np.round(sx - center_x, 2)
    local_y = np.round((sz - min_z) * args.vertical_scale, 2)
    local_z = np.round(sy - center_y, 2)

    flat_points: list[float | int] = []
    for px, py, pz, pr, pg, pb, pc in zip(local_x, local_y, local_z, sr, sg, sb, sc):
        flat_points.extend(
            [float(px), float(py), float(pz), int(pr), int(pg), int(pb), int(pc)]
        )

    payload = {
        "format": "codex-point-cloud-v1",
        "name": f"{source_path.stem} 点云示意",
        "source_file": source_path.name,
        "point_count": int(len(idx)),
        "units": "meters",
        "coordinate_frame": "local-centered",
        "stride": 7,
        "attributes": ["x", "y", "z", "r", "g", "b", "class"],
        "bounds": {
            "min": [float(local_x.min()), float(local_y.min()), float(local_z.min())],
            "max": [float(local_x.max()), float(local_y.max()), float(local_z.max())],
        },
        "source_bounds": {
            "min": [float(sx.min()), float(sy.min()), float(sz.min())],
            "max": [float(sx.max()), float(sy.max()), float(sz.max())],
        },
        "crop_size_m": float(args.crop_size),
        "vertical_scale": float(args.vertical_scale),
        "points": flat_points,
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {output_path} with {payload['point_count']} points")


if __name__ == "__main__":
    main()
