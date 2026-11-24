# TransJakarta Demand Predictor

## Objective

The project predicts the number of recorded TransJakarta tap-in transactions per
date, corridor, direction, and hour. The target name is `passenger_count`.
This means transaction demand, not the actual number of people onboard a bus.

## Dataset

The original source is `data/raw/transjakarta.csv`. It contains approximately
189,500 records and 22 columns for April 2023. The raw CSV must remain unchanged
and should be loaded only by preprocessing code.

The preliminary observed-hour aggregation is
`data/processed/transjakarta_hourly_aggregated.csv`. The audit summary is
`data/reference/transjakarta_data_audit.csv`. Neither derived file is training
data or a replacement for the raw source.

Payment-card identifiers and names are excluded from preprocessing features.
Missing hourly combinations remain `NaN`; this project does not assume that an
missing record means zero transactions. Lag and rolling values are calculated
only from earlier observations in each corridor-direction sequence.

## Project Structure

```text
ngawibarat/
├── data/
│   ├── raw/             Original source data
│   ├── processed/       Aggregated and feature-engineered outputs
│   └── reference/       Audit/reference summaries
├── notebooks/           Interactive preprocessing work
├── src/                 Modular Python implementation
├── models/              Future trained model artifacts
├── reports/             Future reports and visualizations
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Large datasets should not normally be committed to a public Git repository.
The raw and generated processed CSV files are explicitly excluded by
`.gitignore`. This avoids publishing large datasets in Git history. The data
can instead be shared through Git LFS, a private repository, or an external
data-hosting location. The exclusion is documented here and in `.gitignore`;
no local CSV is silently lost or deleted.

## Run Preprocessing

After installing dependencies:

```powershell
python src/preprocessing.py
```

The script resolves paths from the project root, so it can be run from any
current working directory. It creates the observed hourly aggregation, a panel
that preserves unknown hours as `NaN`, and model-ready rows with complete lag
and rolling features.

### Preprocessing methodology

1. Load `data/raw/transjakarta.csv` without modifying it.
2. Check the schema, missing values, duplicate rows, and duplicate transaction
   IDs.
3. Parse `tapInTime` as a datetime.
4. Exclude rows with a missing or blank `corridorID`; exclude rows with an
   invalid `tapInTime`. Missing tap-out or payment fields do not cause a tap-in
   record to be discarded because the target comes from `tapInTime`.
5. Count transactions per date, corridor, direction, and hour.
6. Build a chronological hourly panel for every observed corridor-direction
   sequence. Unobserved hours remain `NaN`.
7. Add calendar fields and corridor-direction-specific historical features.

### Feature definitions

- `hour`: Hour of the timestamp, from 0 through 23.
- `day_of_week`: Monday-based calendar day from 0 through 6.
- `is_weekend`: 1 for Saturday or Sunday, otherwise 0.
- `lag_1`: The preceding hourly `passenger_count` in the same corridor and
  direction.
- `lag_24`: The `passenger_count` from 24 hourly positions earlier in the same
  corridor and direction.
- `rolling_3`: Mean of the three preceding hourly observations, using no current
  timestamp, for the same corridor and direction.

Lag and rolling features are created with chronological shifts and grouping.
They do not use future observations. A missing hourly target is retained as
`NaN`; it is not replaced with zero because missing data may mean no recorded
transaction or unrecorded activity.

### Validated preprocessing outputs

The first M2 execution reported:

- 189,500 raw rows and 22 columns.
- 6,980 rows excluded because `corridorID` was missing.
- 182,520 clean rows available for aggregation.
- 93,212 observed hourly rows.
- 221 unique corridor IDs.
- 2 directions.
- Date range: April 1–30, 2023.
- 300,024 panel rows.
- 11,194 model-ready rows with complete target and feature values.

The generated 93,212 observed rows match the preliminary aggregation on every
key and `passenger_count`. The preliminary aggregation file is read only and is
not overwritten.

The existing notebook also documents the preprocessing steps. Open it with:

```powershell
jupyter notebook notebooks/preprocessing_transjakarta.ipynb
```

Its data path was updated for the `notebooks/` location. The original notebook
content was backed up outside the project before that update.

## Current Development Status

- Workspace organized.
- Raw, preliminary aggregation, audit, and notebook preserved.
- Modular preprocessing implementation initialized.
- Training and evaluation files are placeholders only.
- No model has been trained and no metrics have been invented.

## Known Limitations

- Missing hourly records may represent no transactions or unrecorded data.
- This dataset measures tap-in transaction demand, not actual bus occupancy.
- The available period is one month, April 2023.
- The code is an initial pipeline and has not yet been used for model
  benchmarking.
