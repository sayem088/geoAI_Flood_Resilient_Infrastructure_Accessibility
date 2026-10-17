# GeoAI Flood Dhaka — SCA26

> **Reproducibility code** for the paper:  
> **"Flood Resilient Infrastructure Accessibility in Megacity Dhaka: A Spatially Constrained GeoAI Approach"**  
> *11th International Conference on Smart Cities and Applications (SCA26), Springer Lecture Notes in Networks and Systems (LNNS), 2026*

---

## 📄 Paper Abstract

Monsoon flooding in Dhaka, Bangladesh, isolates vulnerable communities from safe drinking water (WASH), emergency shelters, and waste disposal facilities. This paper presents a GeoAI framework integrating **Sentinel-1 SAR**, **Copernicus DEM**, and **Dynamic World land cover** to predict flood occurrence (S_flood ∈ [0, 1]) across Dhaka's urban core (304.51 km², 11.72M residents). Spatial Block 4-Fold Cross-Validation reveals that random splitting **inflates XGBoost ROC-AUC by 0.0571** (0.9298 vs. 0.8726 ± 0.0541). TreeSHAP identifies imperviousness as the primary predictor (mean|φ| = 2.0095), exceeding elevation attribution threefold. The **Dynamic Environmental Inaccessibility Index (DEII)** models network disruption: monsoon flooding cuts off **1,048,747 residents** from safe water (−15.4%) and **685,281 from shelters** (−8.0%), while **922,000 residents** near municipal landfills face flood-exposure hazards.

---

## 🗺️ Study Area

| Jurisdiction | Area (km²) | Population |
|:---|:---:|:---:|
| Dhaka North City Corporation (DNCC) | 205.49 | ~8.0M |
| Dhaka South City Corporation (DSCC) | 99.02 | ~3.7M |
| **Combined Urban Core** | **304.51** | **11,722,702** |

Coordinate Reference System: **EPSG:32646** (WGS 84 / UTM Zone 46N)

---

## 🏗️ Repository Architecture

```
geoai_flood_dhaka_sca26/
│
├── config.py                        ← All shared paths, constants, hyperparameters
├── master_pipeline.py               ← Root runner (--step / --from / --skip-gee)
├── requirements.txt
├── .gitignore
│
├── 01_data_collection/
│   ├── s01_gee_download_dem_lulc_sar.py     ← GEE: ds_04, ds_05, ds_06
│   ├── s01_gee_editor_script.js             ← Paste-in GEE Code Editor script
│   ├── s01_osm_extract_infrastructure.py    ← Overpass API: ds_03
│   ├── s01_preprocess_admin_boundary.py     ← ds_01
│   ├── s01_preprocess_population.py         ← ds_02
│   ├── s01_preprocess_dem_slope_twi.py      ← DEM → Slope + TWI
│   ├── s01_preprocess_infrastructure.py     ← Infrastructure normalisation
│   ├── s01_audit_datasets.py                ← Health check (exit 1 on failure)
│   └── master_step_01.py
│
├── 02_sampling/
│   ├── s02_extract_training_samples.py      ← Balanced N=20,000 spatial sample
│   ├── s02_compute_moran_spatial_blocks.py  ← Moran's I + 4-quadrant blocks
│   └── master_step_02.py
│
├── 03_modeling/
│   ├── s03_train_xgboost_rf_cv.py           ← RF + XGBoost; Random vs. Spatial CV
│   ├── s03_generate_fig1_roc_curves.py      ← Figure 1: ROC + leakage gap
│   ├── s03_generate_fig2_shap_beeswarm.py   ← Figure 2: TreeSHAP beeswarm
│   └── master_step_03.py
│
├── 04_hazard_mapping/
│   ├── s04_predict_flood_surface.py         ← Wall-to-wall P_flood raster
│   ├── s04_generate_fig3_hazard_map.py      ← Figure 3: Cartographic map
│   └── master_step_04.py
│
├── 05_deii_routing/
│   ├── s05_compute_deii_surface.py          ← DEII 5-band raster
│   ├── s05_compute_catchment_collapse.py    ← Tables 3 + sensitivity analysis
│   └── master_step_05.py
│
├── data/
│   └── datasets/                            ← ds_01 (GeoJSON) + ds_03 (GeoJSON)
│                                              ds_04–06 GeoTIFFs are gitignored
│
├── outputs/
│   ├── figures/                             ← fig1 to fig5 (committed)
│   └── tables/                             ← table_1 to table_5 (committed)
│
└── docs/
    └── data_dictionary.md
```

---


## 📜 License

This code is released for **academic reproducibility** of the SCA26 paper.  
Satellite data are subject to their respective source licenses  
(Copernicus Open Access, Google Earth Engine Terms, OpenStreetMap ODbL).
