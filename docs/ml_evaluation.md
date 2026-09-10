# Machine Learning Model Evaluation Report

## 1. Overview & Setup

```text
5,000 chronological transactions
       │
       ▼
 ┌─────┴─────┐
 │           │
4,000 train  1,000 test
 │           │
 ▼           │
Train model  │
 │           │
 └─────┬─────┘
       ▼
 Model -> Test
       │
       ▼
 Final metrics
```

- **Model Type:** Isolation Forest (`sklearn.ensemble.IsolationForest`)
- **Model Version:** `v1.0.0`
- **Total Dataset Size:** 5,000 transactions
- **Evaluation Methodology:** Chronological 80/20 Train/Test Split (Held-Out Evaluation)
- **Training Set Size:** 4,000 transactions (first 80% chronologically)
- **Held-Out Test Set Size:** 1,000 transactions (last 20% chronologically)
- **Test Set Breakdown:** 936 normal, 64 anomalous (6.4% anomaly ratio)
- **Feature Count:** 8 features
- **Features Used:** `amount, hour_of_day, day_of_week, user_tx_count_24h, amount_deviation, is_new_device, is_new_location, failed_attempts_count`
- **Contamination Parameter:** 0.05
- **Random Seed:** 42
- **Data Leakage Safeguard:** Historical-only rolling feature construction with strict temporal ordering; test set evaluated on genuinely held-out transactions.

---

## 2. Quantitative Performance Metrics (Held-Out Test Set)

| Metric | Score | Explanation |
|---|---|---|
| **Precision** | **0.9583** (95.8%) | Proportion of predicted anomalies in test set that were actual anomalies |
| **Recall** | **0.7188** (71.9%) | Proportion of actual test set anomalies successfully captured |
| **F1-Score** | **0.8214** | Harmonic mean of precision and recall on held-out test data |
| **ROC-AUC** | **0.9740** | Area under the Receiver Operating Characteristic curve on test data |
| **Accuracy** | **0.9800** | Overall classification accuracy across test set transactions |

---

## 3. Confusion Matrix (Held-Out Test Set: 1,000 Transactions)

| | Predicted Normal | Predicted Anomaly |
|---|---|---|
| **Actual Normal** | **934** (TN) | **2** (FP) |
| **Actual Anomaly** | **18** (FN) | **46** (TP) |

- **True Negatives (TN):** 934 legitimate transactions correctly classified as normal.
- **False Positives (FP):** 2 normal transactions flagged as suspicious (investigated by analysts).
- **False Negatives (FN):** 18 anomalies missed by unsupervised ML (covered by deterministic rules).
- **True Positives (TP):** 46 anomalous transactions successfully captured.

---

## 4. Anomaly Type Detection Breakdown (Held-Out Test Set)

| Anomaly Type | Test Samples | Detected | Detection Rate (%) |
|---|---|---|---|
| `FAILED_ATTEMPT_STUFFING` | 8 | 6 | **75.0%** |
| `HIGH_AMOUNT_SPIKE` | 16 | 14 | **87.5%** |
| `LOCATION_HOPPING` | 9 | 6 | **66.67%** |
| `RAPID_BURST` | 11 | 0 | **0.0%** |
| `UNRECOGNIZED_DEVICE` | 20 | 20 | **100.0%** |

---

## 5. Technical Limitations & Hybrid System Discussion

1. **Unsupervised Anomaly Trade-Offs:** Isolation Forest learns data isolation geometry rather than explicit class boundaries. It detects zero-day and multi-feature distributional anomalies without requiring labeled historical fraud.
2. **Hybrid Architecture Advantage:** Standalone ML recall on complex velocity patterns is supplemented by deterministic business rules (`HighAmountRule`, `RapidTransactionsRule`, `NewDeviceRule`, `LocationAnomalyRule`, `FailedAttemptRule`). Even when subtle behavioral anomalies score moderate on ML, deterministic rules catch clear policy violations.
3. **Operational Thresholding:** In the hybrid scoring formula ($0.60 \times \text{Rule} + 0.40 \times \text{ML}$), transactions scoring above 60 trigger alerts for human analyst review.
