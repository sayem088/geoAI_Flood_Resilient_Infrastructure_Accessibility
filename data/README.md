# Data Directory Overview

This directory contains the primary inputs and intermediate processed data used across the GeoAI Flood Dhaka pipeline.

```
data/
├── README.md                      ← This documentation file
├── datasets/                      ← Primary input datasets (ds_01 to ds_06)
│   ├── ds_01_admin_boundary.geojson                     (Committed)
│   ├── ds_02_population_worldpop_100m.tif               (Gitignored)
│   ├── ds_03_critical_environmental_infrastructure.geojson (Committed)
│   ├── ds_04_copernicus_dem_30m.tif                     (Gitignored)
│   ├── ds_05_dynamic_world_lulc_30m.tif                 (Gitignored)
│   └── ds_06_sentinel1_sar_flood_extent_30m.tif         (Gitignored)
└── processed/                     ← Pipeline intermediate outputs (Gitignored)
    ├── dhaka_flood_training_samples.csv
    ├── dhaka_flood_training_samples.geojson
    ├── geoai_flood_model.joblib
    ├── dhaka_flood_susceptibility_probability_30m.tif
    └── dhaka_deii_accessibility_30m.tif
```

---

## Obtaining the Datasets

### Automatic Download via Pipeline
If you have Google Earth Engine access configured:
```bash
python 01_data_collection/master_step_01.py
```
This script downloads `ds_04`, `ds_05`, and `ds_06` via the GEE Python API, extracts OSM infrastructure via Overpass API for `ds_03`, and validates all files with `s01_audit_datasets.py`.

### Manual Download Links
If downloading manually:
1. **ds_01 (Admin Boundary)**: Already provided in `data/datasets/ds_01_admin_boundary.geojson`.
2. **ds_02 (WorldPop)**: Download Bangladesh 2020 100m constrained individual countries raster from [WorldPop](https://www.worldpop.org/project/categories?id=3).
3. **ds_03 (OSM Infrastructure)**: Query via Overpass Turbo or run `01_data_collection/s01_osm_extract_infrastructure.py`.
4. **ds_04 (Copernicus DEM)**: GEE asset `COPERNICUS/DEM/GLO30_COG`.
5. **ds_05 (Dynamic World)**: GEE asset `GOOGLE/DYNAMICWORLD/V1`.
6. **ds_06 (Sentinel-1 SAR)**: GEE asset `COPERNICUS/S1_GRD` (VH polarization, IW mode).

---

## Coordinate Reference System
All spatial files must be projected to **EPSG:32646** (WGS 84 / UTM Zone 46N) at **30m resolution** (100m for population).
Run `python 01_data_collection/s01_audit_datasets.py` at any time to verify CRS, bounding box, dimensions, and band configurations.
