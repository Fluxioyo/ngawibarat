# M2.1 Temporal Feature Audit

## Scope

This audit inspects `src/preprocessing.py` and the generated processed datasets.
It does not change source data or fabricate missing observations.

## 1. Model-ready coverage

- Total model-ready rows: **11,194**
- Corridors with model-ready rows: **221**
- Directions with model-ready rows: **2**

### Rows by direction

- Direction `0.0`: **5628** model-ready rows
- Direction `1.0`: **5566** model-ready rows

### Corridors below usability thresholds

- Fewer than 10 rows: **6** corridors
- Fewer than 20 rows: **20** corridors
- Fewer than 50 rows: **115** corridors

### Observations per corridor

- Minimum: **1**
- Median: **48.00**
- Mean: **50.65**
- Maximum: **127**

### Corridor-direction combinations

Observed corridor-direction combinations: **442**

Combinations with zero usable model-ready observations: **1**

Examples:

- Corridor `M13`, direction `1.0`

Detailed coverage is saved in `reports/model_ready_coverage.csv`.

## 2. Lag and rolling semantics

The implementation sorts by corridor, direction, and timestamp, then uses:

```python
featured["lag_1"] = grouped.shift(1)
featured["lag_24"] = grouped.shift(24)
featured["rolling_3"] = grouped.transform(
    lambda series: series.shift(1).rolling(window=3, min_periods=3).mean()
)
```

### Methodological result

- **lag_1**: NOT guaranteed to represent exactly one calendar hour. It is a
  one-row shift across the chronological panel.
- **lag_24**: NOT guaranteed to represent exactly 24 calendar hours. It is a
  24-row shift.
- **rolling_3**: NOT guaranteed to represent exactly the three immediately
  preceding calendar hours. It is a shifted rolling mean over three panel rows
  with at least three non-missing passenger-count values.

### Empirical exact-calendar verification

Among model-ready rows:

- Exact calendar lag-1 matches: **11,194 of 11,194**
- Exact calendar lag-24 matches: **11,194 of 11,194**
- Exact three preceding-calendar-hour rolling matches:
  **11,194 of 11,194**

The exact checks match features against the timestamped panel by subtracting
1, 24, and 1/2/3 hours while preserving corridor and direction.

## 3. Missing-hour interpretation

Available project documentation and the audit summary do not demonstrate that
missing corridor-hour combinations mean zero transactions. The README and
notebook explicitly preserve them as unknown/`NaN`. The audit contains only
missing-field counts and aggregated nonzero groups.

The unknown/`NaN` interpretation is therefore retained.

## 4. Suitability assessment

The dataset is usable only for a **limited experimental baseline** if the
current lag names are treated as historical panel availability features rather
than exact calendar-time features.

It is not suitable for a rigorous claim that `lag_1`, `lag_24`, or `rolling_3`
represents exact temporal history until timestamp-based lags are implemented.

## Unresolved limitations

- Lags are row-based instead of calendar-timestamp based.
- Rolling features can cross missing hourly observations.
- Missing hours have unknown meaning.
- Corridors have uneven model-ready coverage.
- Data covers only April 2023.
- `passenger_count` is tap-in transaction demand, not onboard occupancy.
- No chronological out-of-time model validation was performed.

No models were trained.
