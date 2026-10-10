# 🌱 Agro Smart - POC (Sidi Moussa)

Proof of concept for smart agriculture from satellite imagery.
From the provided scene, the project computes **NDVI**, separates water / bare soil / vegetation
classes, and splits the area into zones with a simple advisory (critical / watch / ok / healthy).

## Data
`data/sidi_moussa.pdf` contains 3 raster layers (extracted into `data/`):
| File | Content |
|---|---|
| `band_nir.png` | Near-infrared band (grayscale) |
| `band_red.png` | Red band (grayscale) |
| `ndvi_reference.png` | Colourised NDVI shipped with the scene (used for visual validation) |

`NDVI = (NIR - Red) / (NIR + Red)`

## Run
```bash
pip install -r requirements.txt
python run_poc.py            # writes outputs/ (maps, report.json, zones.csv)
streamlit run app.py         # interactive dashboard
```
Optional: `python run_poc.py --pixel-size-m 100` to get areas in km².

## Pipeline
1. Load NIR + Red bands → compute NDVI
2. Water mask (very low NIR: sea + dams)
3. Classify: bare (<0.10), sparse (0.10-0.25), moderate (0.25-0.40), dense (>0.40)
4. Split into an n×n grid, compute mean NDVI per zone → advisory

## Limitations (POC)
- Bands are 8-bit stretched images, not calibrated reflectance → NDVI values are **relative**.
- No georeferencing: zones are image cells, not map coordinates.
- Thresholds are generic, not crop-specific.

## Next steps
Use Sentinel-2 (B4/B8) GeoTIFFs with CRS, time series for trend detection, crop-specific thresholds,
weather/soil-moisture data, and alerts to farmers (SMS / mobile app).
