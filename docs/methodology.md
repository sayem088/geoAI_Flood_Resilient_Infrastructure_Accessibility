# Methodology: Spatially Constrained GeoAI Pipeline

This document provides a concise mathematical and procedural overview of the GeoAI framework implemented in this repository, exactly as published in the SCA26 paper.

---

## 1. Ground Truth Flood Extraction (Sentinel-1 SAR)

Flood inundation is mapped using dual-date Sentinel-1 C-Band synthetic aperture radar (SAR) in Interferometric Wide (IW) swath mode with vertical-horizontal (VH) cross-polarization:

$$\Delta \sigma^0_{\text{VH}} = \sigma^0_{\text{monsoon}} - \sigma^0_{\text{dry}}$$

Where:
- $\sigma^0_{\text{monsoon}}$ is the speckle-filtered median VH backscatter during peak monsoon (July 1 – August 31, 2022).
- $\sigma^0_{\text{dry}}$ is the speckle-filtered median VH backscatter during the dry pre-monsoon baseline (January 1 – April 30, 2022).
- A pixel is classified as flooded if $\Delta \sigma^0_{\text{VH}} < -1.5\text{ dB}$ on normally dry urban land.
- Permanent water bodies are identified using pre-monsoon backscatter ($\sigma^0_{\text{dry}} < -18.0\text{ dB}$) and excluded.

---

## 2. Spatial Feature Engineering

Four globally transferable conditioning covariates are computed at 30m resolution in EPSG:32646 (UTM Zone 46N):

1. **Elevation ($z$, meters)**: Copernicus GLO-30 Digital Elevation Model.
2. **Slope ($\beta$, degrees)**:
   $$\beta = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right) \times \frac{180}{\pi}$$
3. **Topographic Wetness Index ($\text{TWI}$)**:
   $$\text{TWI} = \ln\left(\frac{a}{\tan \beta}\right)$$
   where $a$ is the specific catchment area (approximated locally as $1 / \text{cell\_size}$).
4. **Impervious Surface Fraction ($\text{Built}$, $[0, 1]$)**: Dynamic World near-real-time 10m LULC aggregated to 30m, representing artificial sealed ground that inhibits infiltration.

---

## 3. Spatial Block Cross-Validation (Leakage Control)

To adhere to Tobler's First Law of Geography and prevent overoptimistic evaluation from spatial autocorrelation:
- The study domain is partitioned into 4 non-overlapping geographic quadrants (SW, NW, SE, NE) using median Easting ($X_{\text{median}} = 237,842\text{ m}$) and Northing ($Y_{\text{median}} = 2,631,105\text{ m}$).
- Cross-validation trains on 3 spatial blocks and tests on the remaining unseen spatial block ($K=4$).
- Spatial autocorrelation is quantified using Global Moran's $I$:
  $$I = \frac{N}{S_0} \frac{\sum_i \sum_j w_{ij}(y_i - \bar{y})(y_j - \bar{y})}{\sum_i (y_i - \bar{y})^2}$$
  Result: $I = 0.482$, $z = 64.12$, $p < 0.001$, confirming strong spatial clustering that inflates random CV ROC-AUC by $+0.0571$.

---

## 4. TreeSHAP Explainability

Global and local feature attributions are computed via TreeSHAP (Tree-based Shapley Additive Explanations):
$$f(x) = \phi_0 + \sum_{i=1}^M \phi_i(x)$$
Where $\phi_i(x)$ is the marginal attribution of feature $i$.
- **Impervious Built-Up Fraction**: $\text{mean}|\phi| = 2.0095$ (Primary driver, exceeds elevation threefold).
- **Elevation**: $\text{mean}|\phi| = 0.6558$.
- **Slope**: $\text{mean}|\phi| = 0.3129$.
- **TWI**: $\text{mean}|\phi| = 0.1874$.

---

## 5. Dynamic Environmental Inaccessibility Index (DEII)

To evaluate how monsoon inundation isolates urban residents from critical infrastructure:

1. **Baseline Travel Distance (Dry)**:
   $$d_{ij} = \min_{j} \|p_i - q_j\|$$
   where $p_i$ is population cell $i$ and $q_j$ is facility location $j$.

2. **Monsoon Travel Impedance**:
   $$d'_{ij} = d_{ij} \times (1 + \alpha \cdot P_{\text{flood}, i})$$
   where $\alpha = 3.0$ represents walking speed deceleration and detour overhead.

3. **Critical Route Severance**:
   $$\text{If } P_{\text{flood}, i} \ge \tau_{\text{closure}} \ (0.70), \quad d'_{ij} \to \infty$$
   representing unpassable deep waterlogging where pedestrian and emergency vehicle transit completely collapses.
