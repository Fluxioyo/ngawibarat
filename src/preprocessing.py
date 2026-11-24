"""Load, clean, aggregate, and feature-engineer TransJakarta tap-in data."""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "transjakarta.csv"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
PRELIMINARY_AGGREGATION_PATH = (
    PROCESSED_DATA_DIR / "transjakarta_hourly_aggregated.csv"
)
HOURLY_OUTPUT_PATH = (
    PROCESSED_DATA_DIR / "transjakarta_hourly_observed.csv"
)
PANEL_OUTPUT_PATH = PROCESSED_DATA_DIR / "transjakarta_hourly_panel.csv"
MODEL_OUTPUT_PATH = PROCESSED_DATA_DIR / "transjakarta_model_ready.csv"

REQUIRED_COLUMNS = ("corridorID", "direction", "tapInTime")
GROUP_COLUMNS = ("date", "corridorID", "direction", "hour")
GROUP_KEYS = ("corridorID", "direction")


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the original transaction dataset."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Raw dataset not found: {path}. "
            "The raw CSV is the original source of truth."
        )
    return pd.read_csv(path)


def inspect_data_quality(df: pd.DataFrame) -> dict[str, object]:
    """Return basic quality information without changing the source data."""
    missing = df.isna().sum()
    missing_info = missing[missing > 0].to_dict()
    duplicate_trans_ids = (
        int(df["transID"].duplicated().sum())
        if "transID" in df.columns
        else None
    )
    return {
        "shape": df.shape,
        "missing_values": missing_info,
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_trans_ids": duplicate_trans_ids,
        "dtypes": df.dtypes.astype(str).to_dict(),
    }


def clean_and_parse_with_audit(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean required fields and separately report each exclusion reason."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    work = df[list(REQUIRED_COLUMNS)].copy()
    parsed_time = pd.to_datetime(work["tapInTime"], errors="coerce")

    missing_corridor = work["corridorID"].isna()
    blank_corridor = work["corridorID"].notna() & (
        work["corridorID"].astype(str).str.strip() == ""
    )
    invalid_time = parsed_time.isna()

    audit = {
        "missing_corridorID": int(missing_corridor.sum()),
        "blank_corridorID": int(blank_corridor.sum()),
        "invalid_tapInTime": int(invalid_time.sum()),
    }

    work["tapInTime"] = parsed_time
    work = work.loc[
        ~missing_corridor & ~blank_corridor & ~invalid_time
    ].copy()
    work["corridorID"] = work["corridorID"].astype(str).str.strip()
    audit["rows_excluded_total"] = (
        int(missing_corridor.sum())
        + int(blank_corridor.sum())
        + int(invalid_time.sum())
    )
    audit["rows_excluded_rows_with_overlap"] = int(
        (missing_corridor | blank_corridor | invalid_time).sum()
    )
    return work, audit


def aggregate_hourly(work: pd.DataFrame) -> pd.DataFrame:
    """Count observed tap-in transactions for each date/corridor/direction/hour."""
    work = work.copy()
    work["date"] = work["tapInTime"].dt.floor("D")
    work["hour"] = work["tapInTime"].dt.hour

    hourly = (
        work.groupby(list(GROUP_COLUMNS), dropna=False)
        .size()
        .reset_index(name="passenger_count")
        .sort_values(["corridorID", "direction", "date", "hour"])
        .reset_index(drop=True)
    )
    hourly["day_of_week"] = hourly["date"].dt.day_of_week
    hourly["is_weekend"] = (hourly["day_of_week"] >= 5).astype(int)
    return hourly


def build_hourly_panel(hourly: pd.DataFrame) -> pd.DataFrame:
    """Build an hourly timeline while preserving unknown hours as NaN."""
    panel_parts: list[pd.DataFrame] = []

    for (corridor, direction), group in hourly.groupby(
        list(GROUP_KEYS), dropna=False
    ):
        group = group.sort_values(["date", "hour"]).copy()
        start = group["date"].min()
        end = group["date"].max()
        full_hours = pd.date_range(
            start=start,
            end=end + pd.Timedelta(hours=23),
            freq="h",
        )
        temp = group.set_index(
            group["date"] + pd.to_timedelta(group["hour"], unit="h")
        )
        temp = temp[["passenger_count"]].reindex(full_hours)
        temp.index.name = "timestamp"
        temp = temp.reset_index()
        temp["corridorID"] = corridor
        temp["direction"] = direction
        panel_parts.append(temp)

    if not panel_parts:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "passenger_count",
                "corridorID",
                "direction",
            ]
        )

    panel = pd.concat(panel_parts, ignore_index=True)
    panel["date"] = panel["timestamp"].dt.floor("D")
    panel["hour"] = panel["timestamp"].dt.hour
    panel["day_of_week"] = panel["timestamp"].dt.day_of_week
    panel["is_weekend"] = (panel["day_of_week"] >= 5).astype(int)
    return panel.sort_values(
        ["corridorID", "direction", "timestamp"]
    ).reset_index(drop=True)


def create_historical_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Create shifted lag and rolling features without using future observations."""
    featured = panel.copy().sort_values(
        ["corridorID", "direction", "timestamp"]
    )
    grouped = featured.groupby(list(GROUP_KEYS), dropna=False)["passenger_count"]

    featured["lag_1"] = grouped.shift(1)
    featured["lag_24"] = grouped.shift(24)
    featured["rolling_3"] = grouped.transform(
        lambda series: series.shift(1).rolling(window=3, min_periods=3).mean()
    )
    return featured


def save_processed_outputs(
    hourly: pd.DataFrame,
    panel: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Path]]:
    """Save observed aggregation, panel, and complete model-ready rows."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    hourly.to_csv(HOURLY_OUTPUT_PATH, index=False)
    panel.to_csv(PANEL_OUTPUT_PATH, index=False)

    feature_columns = [
        "corridorID",
        "direction",
        "hour",
        "day_of_week",
        "is_weekend",
        "lag_1",
        "lag_24",
        "rolling_3",
    ]
    model_data = panel.dropna(
        subset=["passenger_count", "lag_1", "lag_24", "rolling_3"]
    ).copy()
    model_data[
        feature_columns + ["passenger_count", "date", "timestamp"]
    ].to_csv(MODEL_OUTPUT_PATH, index=False)

    paths = {
        "hourly": HOURLY_OUTPUT_PATH,
        "panel": PANEL_OUTPUT_PATH,
        "model_ready": MODEL_OUTPUT_PATH,
    }
    return model_data, paths


def compare_to_preliminary(hourly: pd.DataFrame) -> dict[str, object]:
    """Compare preliminary aggregation keys and counts without overwriting it."""
    if not PRELIMINARY_AGGREGATION_PATH.is_file():
        return {
            "preliminary_file_exists": False,
            "comparison_status": "not_available",
        }

    preliminary = pd.read_csv(PRELIMINARY_AGGREGATION_PATH)
    required = ["date", "corridorID", "direction", "hour", "passenger_count"]
    missing_columns = [column for column in required if column not in preliminary]
    if missing_columns:
        return {
            "preliminary_file_exists": True,
            "comparison_status": "incomplete_preliminary_schema",
            "missing_columns": missing_columns,
        }

    preliminary = preliminary[required].copy()
    preliminary["date"] = pd.to_datetime(preliminary["date"], errors="coerce")
    preliminary["corridorID"] = preliminary["corridorID"].astype(str).str.strip()
    preliminary["hour"] = pd.to_numeric(preliminary["hour"], errors="coerce")

    generated = hourly[required].copy()
    generated["corridorID"] = generated["corridorID"].astype(str).str.strip()
    key_columns = ["date", "corridorID", "direction", "hour"]

    merged = generated.merge(
        preliminary,
        on=key_columns,
        how="outer",
        suffixes=("_generated", "_preliminary"),
        indicator=True,
    )
    count_mismatches = int(
        (
            merged["_merge"].eq("both")
            & (
                merged["passenger_count_generated"]
                != merged["passenger_count_preliminary"]
            )
        ).sum()
    )
    matching_keys = int(merged["_merge"].eq("both").sum())

    return {
        "preliminary_file_exists": True,
        "preliminary_rows": len(preliminary),
        "generated_rows": len(generated),
        "only_in_generated": int(merged["_merge"].eq("left_only").sum()),
        "only_in_preliminary": int(merged["_merge"].eq("right_only").sum()),
        "matching_keys": matching_keys,
        "passenger_count_mismatches": count_mismatches,
        "comparison_status": (
            "match"
            if (
                len(preliminary) == len(generated)
                and matching_keys == len(generated)
                and count_mismatches == 0
            )
            else "discrepancy"
        ),
    }


def validate_outputs(
    raw: pd.DataFrame,
    work: pd.DataFrame,
    hourly: pd.DataFrame,
    panel: pd.DataFrame,
    model_data: pd.DataFrame,
    cleaning_audit: dict[str, int],
) -> dict[str, object]:
    """Validate counts, missing values, date range, and temporal ordering."""
    panel_missing = panel.isna().sum()
    model_missing = model_data.isna().sum()
    sorted_panel = panel.sort_values(
        ["corridorID", "direction", "timestamp"]
    ).copy()
    timestamps_monotonic = sorted_panel.groupby(
        ["corridorID", "direction"],
        dropna=False,
    )["timestamp"].apply(
        lambda timestamps: timestamps.is_monotonic_increasing
    )
    passenger_counts = sorted_panel.groupby(
        ["corridorID", "direction"],
        dropna=False,
    )["passenger_count"]
    expected_lag_1 = passenger_counts.shift(1)
    expected_lag_24 = passenger_counts.shift(24)
    expected_rolling_3 = passenger_counts.transform(
        lambda series: series.shift(1).rolling(
            window=3,
            min_periods=3,
        ).mean()
    )

    lag_1_consistent = (
        (sorted_panel["lag_1"].isna() == expected_lag_1.isna())
        & (
            sorted_panel["lag_1"].isna()
            | sorted_panel["lag_1"].eq(expected_lag_1)
        )
    ).all()
    lag_24_consistent = (
        (sorted_panel["lag_24"].isna() == expected_lag_24.isna())
        & (
            sorted_panel["lag_24"].isna()
            | sorted_panel["lag_24"].eq(expected_lag_24)
        )
    ).all()
    rolling_3_consistent = (
        (sorted_panel["rolling_3"].isna() == expected_rolling_3.isna())
        & (
            sorted_panel["rolling_3"].isna()
            | sorted_panel["rolling_3"].eq(expected_rolling_3)
        )
    ).all()

    return {
        "input_rows": len(raw),
        "clean_rows": len(work),
        "rows_excluded": cleaning_audit,
        "aggregated_rows": len(hourly),
        "unique_corridors": int(hourly["corridorID"].nunique(dropna=True)),
        "unique_directions": int(hourly["direction"].nunique(dropna=True)),
        "directions_present": hourly["direction"].dropna().astype(str).unique().tolist(),
        "date_range": (
            str(hourly["date"].min()),
            str(hourly["date"].max()),
        ),
        "hourly_missing_values": hourly.isna().sum().to_dict(),
        "panel_rows": len(panel),
        "panel_missing_values": panel_missing[panel_missing > 0].to_dict(),
        "model_ready_rows": len(model_data),
        "model_ready_missing_values": model_missing[model_missing > 0].to_dict(),
        "lag_1_rows": int(panel["lag_1"].notna().sum()),
        "lag_24_rows": int(panel["lag_24"].notna().sum()),
        "rolling_3_rows": int(panel["rolling_3"].notna().sum()),
        "panel_timestamp_order_valid": bool(timestamps_monotonic.all()),
        "lag_1_consistent": bool(lag_1_consistent),
        "lag_24_consistent": bool(lag_24_consistent),
        "rolling_3_consistent": bool(rolling_3_consistent),
    }


def run_preprocessing() -> dict[str, object]:
    """Run the complete preprocessing pipeline on the raw dataset."""
    raw = load_raw_data()
    quality = inspect_data_quality(raw)
    work, cleaning_audit = clean_and_parse_with_audit(raw)
    hourly = aggregate_hourly(work)
    panel = build_hourly_panel(hourly)
    featured = create_historical_features(panel)
    model_data, paths = save_processed_outputs(hourly, featured)
    validation = validate_outputs(
        raw,
        work,
        hourly,
        featured,
        model_data,
        cleaning_audit,
    )
    comparison = compare_to_preliminary(hourly)

    return {
        "quality": quality,
        "validation": validation,
        "preliminary_comparison": comparison,
        "paths": paths,
    }


if __name__ == "__main__":
    result = run_preprocessing()
    print(result)
