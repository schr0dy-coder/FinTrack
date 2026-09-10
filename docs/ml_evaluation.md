# Machine Learning Model Evaluation Report

## 1. Overview & Setup

- **Model Type:** Isolation Forest (`sklearn.ensemble.IsolationForest`)
- **Model Version:** `v1.0.0`
- **Dataset Size:** 5,000 transactions (4,700 normal, 300 anomalous)
- **Anomaly Ratio:** 6.0%
- **Feature Count:** 8 features
- **Features Used:** `amount, hour_of_day, day_of_week, user_tx_count_24h, amount_deviation, is_new_device, is_new_location, failed_attempts_count`
- **Contamination Parameter:** 0.05
- **Random Seed:** 42

---

## 2. Quantitative Performance Metrics

| Metric | Score | Explanation |
|---|---|---|
| **Precision** | **0.8840** (88.4%) | Proportion of predicted anomalies that were actual anomalies |
| **Recall** | **0.7367** (73.7%) | Proportion of actual anomalies successfully identified |
| **F1-Score** | **0.8036** | Harmonic mean of precision and recall |
| **ROC-AUC** | **0.9758** | Area under the Receiver Operating Characteristic curve |
| **Accuracy** | **0.9784** | Overall classification accuracy across imbalanced classes |

---

## 3. Confusion Matrix

| | Predicted Normal | Predicted Anomaly |
|---|---|---|
| **Actual Normal** | **4,671** (TN) | **29** (FP) |
| **Actual Anomaly** | **79** (FN) | **221** (TP) |

- **True Negatives (TN):** 4,671 legitimate transactions correctly classified as normal.
- **False Positives (FP):** 29 normal transactions flagged as suspicious (investigated by analysts).
- **False Negatives (FN):** 79 anomalies missed by unsupervised ML (covered by deterministic rules).
- **True Positives (TP):** 221 anomalous transactions successfully captured.

---

## 4. Anomaly Type Detection Breakdown

| Anomaly Type | Total Samples | Detected | Detection Rate (%) |
|---|---|---|---|
| `FAILED_ATTEMPT_STUFFING` | 51 | 46 | **90.2%** |
| `HIGH_AMOUNT_SPIKE` | 62 | 62 | **100.0%** |
| `LOCATION_HOPPING` | 54 | 40 | **74.07%** |
| `RAPID_BURST` | 60 | 2 | **3.33%** |
| `UNRECOGNIZED_DEVICE` | 73 | 71 | **97.26%** |

---

## 5. Technical Limitations & Discussion

1. **Unsupervised Anomaly Trade-Offs:** Isolation Forest learns data isolation geometry rather than explicit class boundaries. It detects zero-day and multi-feature distributional anomalies without requiring labeled historical fraud.
2. **Hybrid Architecture Advantage:** The standalone ML recall is supplemented by deterministic business rules (`HighAmountRule`, `RapidTransactionsRule`, `NewDeviceRule`, `LocationAnomalyRule`, `FailedAttemptRule`). Even when subtle behavioral anomalies score low on ML, deterministic rules catch clear violations.
3. **Operational Thresholding:** In the hybrid scoring formula ($0.60 \times \text{Rule} + 0.40 \times \text{ML}$), transactions scoring above 60 trigger alerts for human analyst review.
