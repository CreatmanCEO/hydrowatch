"""Tool: Validate an uploaded CSV file with groundwater observations."""
from pathlib import Path

import pandas as pd
import numpy as np

from models.schemas import ValidationResult

EXPECTED_COLUMNS = [
    "timestamp", "well_id", "debit_ls", "tds_mgl",
    "ph", "chloride_mgl", "water_level_m", "temperature_c",
]

VALID_RANGES = {
    "debit_ls": (0, 100),
    "tds_mgl": (0, 50000),
    "ph": (0, 14),
    "chloride_mgl": (0, 30000),
    "water_level_m": (0, 500),
    "temperature_c": (0, 60),
}


def validate_csv(
    file_path: str,
    expected_columns: list[str] | None = None,
) -> ValidationResult:
    """Validate a CSV file and return structured result."""
    if expected_columns is None:
        expected_columns = EXPECTED_COLUMNS

    errors = []
    warnings = []

    path = Path(file_path)
    if not path.exists():
        return ValidationResult(
            valid=False, total_rows=0, valid_rows=0,
            errors=[f"File not found: {path.name}"],
        )

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return ValidationResult(
            valid=False, total_rows=0, valid_rows=0,
            errors=[f"Error reading CSV: {str(e)}"],
        )

    total_rows = len(df)

    # Check columns
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing columns: {', '.join(sorted(missing_cols))}")

    extra_cols = set(df.columns) - set(expected_columns)
    if extra_cols:
        warnings.append(f"Extra columns (ignored): {', '.join(sorted(extra_cols))}")

    # Check value ranges
    invalid_rows = set()
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        out_of_range = (numeric < lo) | (numeric > hi)
        nan_mask = numeric.isna() & df[col].notna()

        bad_range_idx = df.index[out_of_range & ~numeric.isna()].tolist()
        bad_parse_idx = df.index[nan_mask].tolist()

        if bad_range_idx:
            errors.append(f"{col}: {len(bad_range_idx)} rows out of range [{lo}, {hi}]")
            invalid_rows.update(bad_range_idx)

        if bad_parse_idx:
            errors.append(f"{col}: {len(bad_parse_idx)} rows with non-numeric values")
            invalid_rows.update(bad_parse_idx)

    # Check timestamp parsing
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        bad_ts = ts.isna().sum()
        if bad_ts > 0:
            warnings.append(f"timestamp: {bad_ts} rows with unparseable dates")

    valid_rows = total_rows - len(invalid_rows)

    # Column stats for numeric columns
    column_stats = {}
    for col in VALID_RANGES:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            column_stats[col] = {
                "min": float(numeric.min()) if not numeric.isna().all() else 0.0,
                "max": float(numeric.max()) if not numeric.isna().all() else 0.0,
                "mean": float(numeric.mean()) if not numeric.isna().all() else 0.0,
            }

    return ValidationResult(
        valid=len(errors) == 0,
        total_rows=total_rows,
        valid_rows=valid_rows,
        errors=errors,
        warnings=warnings,
        column_stats=column_stats,
    )
