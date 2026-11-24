# M3 Exploratory Data Analysis

## Scope and denominators

This report distinguishes three denominators:

- **Raw transactions:** the cleaned raw rows used to form hourly totals.
- **Hourly observed groups:** rows in `transjakarta_hourly_observed.csv`, each representing
  a date-corridor-direction-hour combination with at least one recorded tap-in.
- **Model-ready observations:** rows in `transjakarta_model_ready.csv` with complete
  target and lag features.

Missing panel hours remain `NaN`; they are not counted as zero demand.

## Key findings

### A. Highest corridors

1. Corridor `12H`: **1,253** recorded tap-in transactions
2. Corridor `11`: **1,241** recorded tap-in transactions
3. Corridor `13`: **1,214** recorded tap-in transactions
4. Corridor `JAK.39`: **1,161** recorded tap-in transactions
5. Corridor `5`: **1,148** recorded tap-in transactions
6. Corridor `7`: **1,148** recorded tap-in transactions
7. Corridor `S31`: **1,147** recorded tap-in transactions
8. Corridor `2B`: **1,133** recorded tap-in transactions
9. Corridor `11C`: **1,128** recorded tap-in transactions
10. Corridor `JAK.14`: **1,118** recorded tap-in transactions

### B. Highest-demand hours

The peak hour by total recorded transactions is **hour 06**
with **28,023** recorded tap-ins. Hourly totals include every
corridor and direction in the observed aggregation.

### C. Weekdays versus weekends

- Weekday observed groups: **78,065**; total
  **164,700**; mean **2.11** transactions per observed hourly row.
- Weekend observed groups: **15,147**; total
  **17,820**; mean **1.18** transactions per observed hourly row.

These totals reflect the number and mix of observed hourly groups. The mean is the
more direct scale-adjusted descriptive comparison.

### D. Direction comparison

- Direction `0.0`: **91,285** recorded transactions;
  mean **1.96** per observed hourly row.
- Direction `1.0`: **91,235** recorded transactions;
  mean **1.96** per observed hourly row.

### E. 30-day trend

- Peak day: **2023-04-13**, with
  **9,712** recorded tap-in transactions.
- Lowest day: **2023-04-01**, with
  **48** recorded tap-in transactions.

The trend is descriptive; it does not establish a cause for daily differences.

### F. Limited corridor coverage

A corridor with fewer than 20 usable model-ready observations is treated here as
insufficient for a dependable corridor-specific evaluation.

- Corridor `M13`: **1** model-ready rows
- Corridor `11K`: **4** model-ready rows
- Corridor `6P`: **4** model-ready rows
- Corridor `12F`: **4** model-ready rows
- Corridor `M4`: **7** model-ready rows
- Corridor `JAK.80`: **8** model-ready rows
- Corridor `2A`: **11** model-ready rows
- Corridor `1Q`: **11** model-ready rows
- Corridor `D11`: **11** model-ready rows
- Corridor `M7B`: **12** model-ready rows
- Corridor `JAK.08`: **12** model-ready rows
- Corridor `JAK.28`: **12** model-ready rows
- Corridor `9H`: **13** model-ready rows
- Corridor `JAK.73`: **13** model-ready rows
- Corridor `1T`: **14** model-ready rows
- Corridor `4F`: **15** model-ready rows
- Corridor `JAK.04`: **16** model-ready rows
- Corridor `S21`: **16** model-ready rows
- Corridor `JAK.49`: **17** model-ready rows
- Corridor `JAK.29`: **19** model-ready rows

Coverage summary:

- Corridors below 10 model-ready rows: **6**
- Corridors below 20 model-ready rows: **20**
- Corridors below 50 model-ready rows: **115**

Coverage details are in `reports/model_ready_coverage.csv` and
`reports/eda_summary.csv`.

## Overall descriptive statistics

- Audit raw rows: **189,500**
- Observed hourly rows: **93,212**
- Recorded tap-in transaction total from observed rows: **182,520**
- Panel rows: **300,024**
- Panel rows with observed passenger count: **93,212**
- Panel rows with missing/unknown passenger count: **206,812**
- Model-ready rows: **11,194**

Observed hourly passenger-count distribution:

- Minimum: **1**
- Median: **2.00**
- Mean: **1.96**
- Maximum: **11**

Model-ready target distribution:

- Minimum: **1**
- Median: **2.00**
- Mean: **1.86**
- Maximum: **8**

## Useful future features

Likely useful features for an initial pooled experiment include:

- `hour`
- `day_of_week`
- `is_weekend`
- `corridorID`
- `direction`
- lag and rolling features, with the temporal limitation identified in M2.1

The lag features should not be described as exact calendar-time features until
timestamp-based implementations are added.

## Initial pooled-model suitability

The dataset is suitable for a **limited pooled baseline experiment** if:

- The model uses only `model_ready` rows.
- Corridor and direction are included or encoded carefully.
- Evaluation remains chronological.
- Uneven corridor coverage is reported.
- The missing-hour/feature limitation is stated.

It is not yet suitable for rigorous corridor-specific evaluation for corridors
below the selected coverage threshold.

## Limitations

- `passenger_count` measures tap-in transactions, not bus occupancy.
- Missing hourly observations remain unknown rather than proven zero.
- The exact lag implementation is row-based, not timestamp-based.
- Descriptive totals can reflect number of active corridor-direction groups.
- Only April 2023 is available.
- EDA cannot establish causal relationships.
- Some corridors have very low model-ready coverage.

## Unanswered questions

- What operationally distinguishes missing hours from true zero-demand hours?
- Would a timestamp-based lag implementation change model behavior?
- Should sparse corridors be pooled, excluded, or modeled separately?
- How should missing historical observations be represented in the future model?

No models were trained and no processed outputs were modified.

## Figures

- `reports/figures/hourly_demand_distribution.png`
- `reports/figures/daily_transaction_trend.png`
- `reports/figures/top_10_corridors.png`
- `reports/figures/weekday_vs_weekend.png`
- `reports/figures/direction_comparison.png`
- `reports/figures/model_ready_coverage_distribution.png`
- `reports/figures/passenger_count_distribution.png`
