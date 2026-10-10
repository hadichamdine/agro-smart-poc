"""Agro Smart POC - NDVI analysis core (numpy / Pillow / matplotlib)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image

DATA = Path(__file__).resolve().parent.parent / "data"

# class id -> (label, NDVI lower bound, RGB colour)
CLASSES = {
    0: ("Water", None, (49, 99, 175)),
    1: ("Bare / dry soil", -1.0, (230, 190, 130)),
    2: ("Sparse vegetation", 0.10, (240, 230, 120)),
    3: ("Moderate vegetation", 0.25, (140, 200, 80)),
    4: ("Dense vegetation", 0.40, (30, 130, 50)),
}
WATER_NIR_MAX = 25  # NIR digital number below which a pixel is treated as water


def load_bands(data_dir: Path = DATA):
    nir = np.asarray(Image.open(data_dir / "band_nir.png").convert("L"), dtype=float)
    red = np.asarray(Image.open(data_dir / "band_red.png").convert("L"), dtype=float)
    return nir, red


def compute_ndvi(nir, red):
    return (nir - red) / (nir + red + 1e-6)


def water_mask(nir):
    return nir < WATER_NIR_MAX


def classify(ndvi, water):
    cls = np.full(ndvi.shape, 1, dtype=np.uint8)
    for k in (2, 3, 4):
        cls[ndvi >= CLASSES[k][1]] = k
    cls[water] = 0
    return cls


def class_stats(cls, pixel_size_m: float | None = None):
    total = cls.size
    out = {}
    for k, (name, _, _) in CLASSES.items():
        n = int((cls == k).sum())
        row = {"pixels": n, "percent": round(100 * n / total, 2)}
        if pixel_size_m:
            row["area_km2"] = round(n * pixel_size_m**2 / 1e6, 2)
        out[name] = row
    return out


def grid_zones(ndvi, water, cls, n: int = 16):
    """Split the scene into n x n zones and attach a simple advisory to each."""
    h, w = ndvi.shape
    zones = []
    for i in range(n):
        for j in range(n):
            ys, ye = i * h // n, (i + 1) * h // n
            xs, xe = j * w // n, (j + 1) * w // n
            land = ~water[ys:ye, xs:xe]
            if land.mean() < 0.5:  # mostly sea / reservoir
                continue
            m = float(ndvi[ys:ye, xs:xe][land].mean())
            bare = float((cls[ys:ye, xs:xe] == 1).mean())
            if m < 0.12:
                level, advice = "critical", "Very low vegetation - check irrigation / soil"
            elif m < 0.22:
                level, advice = "watch", "Below-average vegetation - monitor water stress"
            elif m < 0.35:
                level, advice = "ok", "Moderate crop vigour"
            else:
                level, advice = "healthy", "Dense, healthy vegetation"
            zones.append({"row": i, "col": j, "mean_ndvi": round(m, 3),
                          "bare_fraction": round(bare, 3),
                          "level": level, "advice": advice})
    return zones


def colorize(cls):
    rgb = np.zeros((*cls.shape, 3), dtype=np.uint8)
    for k, (_, _, col) in CLASSES.items():
        rgb[cls == k] = col
    return rgb


def ndvi_to_rgb(ndvi, water):
    from matplotlib import colormaps

    x = np.clip((ndvi + 0.1) / 0.7, 0, 1)
    rgb = (colormaps["RdYlGn"](x)[..., :3] * 255).astype(np.uint8)
    rgb[water] = CLASSES[0][2]
    return rgb


def run(data_dir: Path = DATA, pixel_size_m: float | None = None, grid: int = 16):
    nir, red = load_bands(data_dir)
    ndvi = compute_ndvi(nir, red)
    water = water_mask(nir)
    cls = classify(ndvi, water)
    land = ~water
    return {
        "ndvi": ndvi, "water": water, "cls": cls,
        "stats": class_stats(cls, pixel_size_m),
        "zones": grid_zones(ndvi, water, cls, grid),
        "summary": {
            "mean_ndvi_land": round(float(ndvi[land].mean()), 3),
            "land_pixels": int(land.sum()),
            "image_size": list(nir.shape[::-1]),
        },
    }


def export(res, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(ndvi_to_rgb(res["ndvi"], res["water"])).save(out_dir / "ndvi_map.png")
    Image.fromarray(colorize(res["cls"])).save(out_dir / "classification_map.png")
    (out_dir / "report.json").write_text(json.dumps(
        {"summary": res["summary"], "classes": res["stats"], "zones": res["zones"]},
        indent=2, ensure_ascii=False))
    with open(out_dir / "zones.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=res["zones"][0].keys())
        wr.writeheader()
        wr.writerows(res["zones"])
