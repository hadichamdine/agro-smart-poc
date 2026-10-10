"""CLI: python run_poc.py [--pixel-size-m 100] [--grid 16]"""
import argparse
from pathlib import Path
from src.analysis import run, export

p = argparse.ArgumentParser()
p.add_argument("--pixel-size-m", type=float, default=None, help="ground size of one pixel (m) to get km2")
p.add_argument("--grid", type=int, default=16)
a = p.parse_args()
res = run(pixel_size_m=a.pixel_size_m, grid=a.grid)
export(res, Path("outputs"))
print("Mean NDVI (land):", res["summary"]["mean_ndvi_land"])
for k, v in res["stats"].items():
    print(f"  {k:22s} {v['percent']:6.2f} %")
crit = [z for z in res["zones"] if z["advice"].startswith("Critical")]
print(f"Zones analysed: {len(res['zones'])} | critical: {len(crit)}")
print("Outputs written to ./outputs")
