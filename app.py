"""Agro Smart POC dashboard:  streamlit run app.py"""
import pandas as pd
import streamlit as st
from PIL import Image

from src.analysis import CLASSES, classify, colorize, ndvi_to_rgb, run

st.set_page_config(page_title="Agro Smart - Sidi Moussa", layout="wide")
st.title("🌱 Agro Smart - Sidi Moussa (POC)")
st.caption("NDVI computed from the NIR and Red bands of a satellite scene.")

with st.sidebar:
    px = st.number_input("Pixel size (m), 0 = unknown", 0.0, 1000.0, 0.0, 10.0)
    grid = st.slider("Zone grid (n x n)", 8, 32, 16)
    t_sparse = st.slider("Sparse vegetation NDVI >=", 0.0, 0.3, 0.10, 0.01)
    t_mod = st.slider("Moderate vegetation NDVI >=", 0.1, 0.5, 0.25, 0.01)
    t_dense = st.slider("Dense vegetation NDVI >=", 0.2, 0.7, 0.40, 0.01)

CLASSES[2] = (CLASSES[2][0], t_sparse, CLASSES[2][2])
CLASSES[3] = (CLASSES[3][0], t_mod, CLASSES[3][2])
CLASSES[4] = (CLASSES[4][0], t_dense, CLASSES[4][2])
res = run(pixel_size_m=px or None, grid=grid)

c1, c2, c3 = st.columns(3)
c1.image(Image.open("data/ndvi_reference.png"), caption="Reference (provided)")
c2.image(ndvi_to_rgb(res["ndvi"], res["water"]), caption="NDVI (computed)")
c3.image(colorize(res["cls"]), caption="Land-cover / vigour classes")

st.metric("Mean NDVI (land)", res["summary"]["mean_ndvi_land"])
st.subheader("Class statistics")
st.dataframe(pd.DataFrame(res["stats"]).T)

st.subheader("Zone advisories")
zones = pd.DataFrame(res["zones"])
lvl = st.multiselect("Level", ["critical", "watch", "ok", "healthy"], ["critical", "watch"])
st.dataframe(zones[zones.level.isin(lvl)].sort_values("mean_ndvi"))
