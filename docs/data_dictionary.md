# Data Dictionary: Standardized Research Datasets

All primary input datasets for this research study are stored in:
`data/datasets/`

Every primary dataset strictly follows the standardized naming format:
`ds_${num}_${topic}` (zero-padded two digits: `ds_01` through `ds_06`)

> **Architectural Policy**:
> - The `data/datasets/` directory contains strictly and exclusively the 6 primary gathered/preprocessed research datasets (`ds_01` to `ds_06`).
> - Intermediate training samples, GeoAI model checkpoints, continuous hazard probability rasters, and dynamic accessibility network surfaces are strictly stored in `data/processed/`.
> - All outputs (figures and tables) are stored in `outputs/figures/` and `outputs/tables/`.

Target Projected Coordinate Reference System: **`EPSG:32646`** (WGS 84 / UTM Zone 46N, Metric)  
Study Area Bounding Box (WGS84): $[90.32^\circ \text{E}, 23.66^\circ \text{N}, 90.52^\circ \text{E}, 23.91^\circ \text{N}]$  
Metric Extents (UTM Zone 46N): $[226000.0\text{ m}, 2618000.0\text{ m}, 248000.0\text{ m}, 2647000.0\text{ m}]$  
Target Domain: **Dhaka Megacity Urban Core (Dhaka North & Dhaka South City Corporations - DNCC & DSCC)**  
Total Administrative Urban Area: **$304.51\text{ km}^2$**  
Total Enclosed Population: **$11,722,702$ residents**  

---

## Master Dataset Inventory

| Dataset File | Domain & Topic | Source / Sensor | Native Resolution | Coordinate System | Format |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`ds_01_admin_boundary.geojson`** | Administrative Boundaries | UN OCHA / BBS Bangladesh (Admin Level 3) | Vector Polygons (2 City Corps) | `EPSG:4326` -> `EPSG:32646` | GeoJSON |
| **`ds_02_population_worldpop_100m.tif`** | Population Density (Demand) | WorldPop (Univ. of Southampton, 2020) | 100 meters ($290 \times 220$) | `EPSG:4326` -> `EPSG:32646` | GeoTIFF |
| **`ds_03_critical_environmental_infrastructure.geojson`** | WASH, Shelters & Waste Sites | OpenStreetMap (Overpass API live query) | Vector Points (819 nodes) | `EPSG:4326` -> `EPSG:32646` | GeoJSON |
| **`ds_04_copernicus_dem_30m.tif`** | Hydro-Topography (DEM, Slope, TWI) | Copernicus GLO-30 (`COPERNICUS/DEM/GLO30_COG`) | 30 meters ($937 \times 697$) | `EPSG:32646` | Multi-band GeoTIFF |
| **`ds_05_dynamic_world_lulc_30m.tif`** | Impervious Built-Up Fraction | Google Dynamic World (`GOOGLE/DYNAMICWORLD/V1`) | 30 meters ($937 \times 697$) | `EPSG:32646` | GeoTIFF |
| **`ds_06_sentinel1_sar_flood_extent_30m.tif`** | Ground Truth Flood Inundation | Sentinel-1 C-Band SAR (`COPERNICUS/S1_GRD`) | 30 meters ($937 \times 697$) | `EPSG:32646` | Multi-band GeoTIFF |

---

## Detailed Band Specifications

### `ds_01_admin_boundary.geojson`
* **Features**: Dhaka North City Corporation (DNCC, $205.49\text{ km}^2$) and Dhaka South City Corporation (DSCC, $99.02\text{ km}^2$).
* **Key Columns**: `adm3_name`, `adm2_name`, `area_sqkm`, `geometry`.
* **Total Area**: $304.51\text{ km}^2$.

### `ds_02_population_worldpop_100m.tif`
* **Band 1 (`population_count_per_cell`)**: Estimated number of residents per 1-hectare pixel ($100\text{ m} \times 100\text{ m}$).
* **Dimensions**: $290 \times 220$ pixels, mass-conserved ($11,722,702$ total residents enclosed). Peak urban density reaches $3,212$ residents/hectare.

### `ds_03_critical_environmental_infrastructure.geojson`
* **Category Breakdown (819 verified nodes strictly within DNCC & DSCC)**:
  * `Dhaka North City Corporation (DNCC)`: 301 WASH Drinking Water Points, 59 Emergency Shelters, 41 Waste Contamination Sites (Total: **401 nodes**).
  * `Dhaka South City Corporation (DSCC)`: 41 WASH Drinking Water Points, 38 Emergency Shelters, 339 Waste Contamination Sites (Total: **418 nodes**).
  * `Grand Total`: **819 verified nodes** (380 waste sites, 342 WASH water points, 97 emergency shelters).

### `ds_04_copernicus_dem_30m.tif`
* **Band 1 (`elevation_meters`)**: Terrain elevation in meters above sea level ($30\text{ m}$ grid, $937 \times 697$ cells).
* **Band 2 (`slope_degrees`)**: Terrain slope gradient in degrees computed via spatial gradient vectors.
* **Band 3 (`topographic_wetness_index`)**: Topographic Wetness Index: $\text{TWI} = \ln(a / \tan \beta)$.

### `ds_05_dynamic_world_lulc_30m.tif`
* **Band 1 (`impervious_fraction`)**: Continuous built-up probability ($0.0$ to $1.0$) representing artificial sealed surfaces that block infiltration and exacerbate urban waterlogging ($937 \times 697$ cells).

### `ds_06_sentinel1_sar_flood_extent_30m.tif`
* **Band 1 (`flood_ground_truth`)**: Binary flood inundation mask ($1 = \text{Flooded}, 0 = \text{Non-Flooded}$, $937 \times 697$ cells).
* **Band 2 (`vh_diff`)**: Radar backscatter change: $\Delta \sigma^0_{\text{VH}} = \sigma^0_{\text{monsoon}} - \sigma^0_{\text{dry}}$ (in dB).
* **Band 3 (`monsoon_vh`)**: Speckle-filtered median VH backscatter during monsoon peak (July–August 2022).
* **Band 4 (`dry_vh`)**: Speckle-filtered median VH backscatter during dry baseline (Jan–April 2022).
