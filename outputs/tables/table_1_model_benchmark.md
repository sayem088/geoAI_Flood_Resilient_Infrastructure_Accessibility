# Table 1: Comparative Evaluation of GeoAI Models under Random vs. Spatial Block Cross-Validation across 20,000 Ground Truth Points in Dhaka Urban Core

| Algorithm | Validation Protocol | ROC-AUC | F1-Score | Precision | Recall | Brier Score | Leakage Gap ($\Delta$AUC) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest** | Random 4-Fold (Naive) | **0.9302** | 0.8710 | 0.8874 | 0.8554 | 0.0977 | Baseline (Leaked) |
| | Spatial Block 4-Fold | **0.8705** | 0.7948 | 0.8576 | 0.7561 | 0.1039 | **+5.97%** Overestimated |
| **XGBoost** | Random 4-Fold (Naive) | **0.9298** | 0.8709 | 0.8875 | 0.8551 | 0.0975 | Baseline (Leaked) |
| | Spatial Block 4-Fold | **0.8727** | 0.7908 | 0.8529 | 0.7528 | 0.1042 | **+5.71%** Overestimated |

### Spatial Transferability across Quadrants (XGBoost):
- **Block 0 (South-West Basin)**: ROC-AUC = 0.8026 (4,748 test points)
- **Block 1 (North-West Sector)**: ROC-AUC = 0.8622 (5,240 test points)
- **Block 2 (South-East Core)**:   ROC-AUC = 0.9293 (5,243 test points)
- **Block 3 (North-East Fringe)**: ROC-AUC = 0.8964 (4,769 test points)
