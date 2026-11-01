"""Validated data access for the CSV development source and hosted MySQL mode.

The CSV source is intentionally read from the supplied ETL package. Raw files
are never modified by this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_DIR = BASE_DIR / "erp_semester5_etl_package"

REQUIRED_COLUMNS = {
    "students": {
        "Enrollment_No", "Name", "Phone_No", "Email", "Gender",
        "Department", "Section", "Semester", "Address", "Academic_Year", "CGPA",
    },
    "attendance": {"Enrollment_No", "Subject", "Attendance_Percentage"},
    "examination": {
        "Enrollment_No", "Subject", "Internal_Marks", "External_Marks",
        "Total_Marks", "Grade",
    },
    "fees": {
        "Enrollment_No", "Semester", "Total_Fees", "Paid_Amount",
        "Pending_Amount", "Payment_Status",
    },
}

CSV_FILES = {
    "students": "students (2).csv",
    "attendance": "attendance.csv",
    "examination": "examination.csv",
    "fees": "fees.csv",
}


class DataValidationError(ValueError):
    """Raised when the configured source does not satisfy warehouse rules."""


@dataclass(frozen=True)
class DataQuality:
    row_counts: dict[str, int]
    missing_values: dict[str, dict[str, int]]
    duplicate_student_ids: int
    invalid_references: dict[str, int]
    reconciliation_errors: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return {
            "row_counts": self.row_counts,
            "missing_values": self.missing_values,
            "duplicate_student_ids": self.duplicate_student_ids,
            "invalid_references": self.invalid_references,
            "reconciliation_errors": self.reconciliation_errors,
        }


@dataclass
class DataStore:
    students: pd.DataFrame
    attendance: pd.DataFrame
    examination: pd.DataFrame
    fees: pd.DataFrame
    quality: DataQuality

    @classmethod
    def from_csv(cls, directory: str | os.PathLike[str] | None = None) -> "DataStore":
        source_dir = Path(directory or os.getenv("CSV_DATA_DIR", DEFAULT_CSV_DIR))
        frames: dict[str, pd.DataFrame] = {}
        for dataset, filename in CSV_FILES.items():
            path = source_dir / filename
            if not path.is_file():
                raise DataValidationError(f"Missing {dataset} source file: {path}")
            try:
                frames[dataset] = pd.read_csv(path)
            except (OSError, pd.errors.ParserError) as exc:
                raise DataValidationError(f"Unable to read {path}: {exc}") from exc

        _validate_schema(frames)
        _normalize_types(frames)
        quality = _quality_report(frames)
        _validate_quality(quality)
        return cls(quality=quality, **frames)

    def student(self, enrollment_no: str) -> dict[str, Any] | None:
        key = enrollment_no.strip().upper()
        matches = self.students[
            self.students["Enrollment_No"].str.upper() == key
        ]
        if matches.empty:
            return None
        row = _record(matches.iloc[0])
        attendance = self.attendance[
            self.attendance["Enrollment_No"] == row["Enrollment_No"]
        ]
        examination = self.examination[
            self.examination["Enrollment_No"] == row["Enrollment_No"]
        ]
        fees = self.fees[self.fees["Enrollment_No"] == row["Enrollment_No"]]
        fee = _record(fees.iloc[0]) if not fees.empty else None
        return {
            "personal": row,
            "attendance": {
                "records": _records(attendance),
                "average": _rounded_mean(attendance["Attendance_Percentage"]),
                "count": len(attendance),
            },
            "examination": {
                "records": _records(examination),
                "average": _rounded_mean(examination["Total_Marks"]),
                "count": len(examination),
            },
            "fees": fee,
            "source_datasets": [
                {"name": name, "file": f"CSV: {CSV_FILES[name]}", "status": "Found"}
                for name in CSV_FILES
            ],
        }

    def kpis(self) -> dict[str, Any]:
        student_attendance = self.attendance.groupby("Enrollment_No")[
            "Attendance_Percentage"
        ].mean()
        attention_ids = set(student_attendance[student_attendance < 75].index)
        return {
            "total_students": len(self.students),
            "avg_attendance": _rounded_mean(self.attendance["Attendance_Percentage"]),
            "avg_marks": _rounded_mean(self.examination["Total_Marks"]),
            "total_fees": int(self.fees["Total_Fees"].sum()),
            "total_paid": int(self.fees["Paid_Amount"].sum()),
            "total_pending": int(self.fees["Pending_Amount"].sum()),
            "students_requiring_attention": len(attention_ids),
            "departments": sorted(self.students["Department"].dropna().unique().tolist()),
            "sections": sorted(self.students["Section"].dropna().unique().tolist()),
            "semesters": sorted(self.students["Semester"].dropna().unique().tolist()),
            "department_counts": self.students["Department"].value_counts().sort_index().to_dict(),
            "quality": self.quality.as_dict(),
        }


_STORE: DataStore | None = None


def get_store() -> DataStore:
    """Return the process-cached CSV store for development mode."""
    global _STORE
    if _STORE is None:
        _STORE = DataStore.from_csv()
    return _STORE


def clear_store_cache() -> None:
    global _STORE
    _STORE = None


def _validate_schema(frames: dict[str, pd.DataFrame]) -> None:
    for dataset, required in REQUIRED_COLUMNS.items():
        actual = set(frames[dataset].columns)
        missing = sorted(required - actual)
        if missing:
            raise DataValidationError(
                f"{dataset} is missing required columns: {', '.join(missing)}"
            )


def _normalize_types(frames: dict[str, pd.DataFrame]) -> None:
    for frame in frames.values():
        frame["Enrollment_No"] = frame["Enrollment_No"].astype("string").str.strip()
    students = frames["students"]
    students["Semester"] = pd.to_numeric(students["Semester"], errors="coerce").astype("Int64")
    students["CGPA"] = pd.to_numeric(students["CGPA"], errors="coerce")
    for name in ("attendance", "examination", "fees"):
        frame = frames[name]
        for column in frame.columns:
            if column in {"Enrollment_No", "Subject", "Grade", "Payment_Status"}:
                continue
            frame[column] = pd.to_numeric(frame[column], errors="coerce")


def _quality_report(frames: dict[str, pd.DataFrame]) -> DataQuality:
    students = frames["students"]
    student_ids = set(students["Enrollment_No"].dropna())
    invalid_references = {
        name: int((~frame["Enrollment_No"].isin(student_ids)).sum())
        for name, frame in frames.items()
        if name != "students"
    }
    examination = frames["examination"]
    fees = frames["fees"]
    reconciliation_errors = {
        "examination_total": int(
            (examination["Total_Marks"] != examination["Internal_Marks"] + examination["External_Marks"]).sum()
        ),
        "fee_total": int(
            (fees["Total_Fees"] != fees["Paid_Amount"] + fees["Pending_Amount"]).sum()
        ),
    }
    attendance = frames["attendance"]
    if ((attendance["Attendance_Percentage"] < 0) | (attendance["Attendance_Percentage"] > 100)).any():
        reconciliation_errors["attendance_range"] = int(
            ((attendance["Attendance_Percentage"] < 0) | (attendance["Attendance_Percentage"] > 100)).sum()
        )
    if (
        (examination["Internal_Marks"] < 0)
        | (examination["Internal_Marks"] > 40)
        | (examination["External_Marks"] < 0)
        | (examination["External_Marks"] > 60)
        | (examination["Total_Marks"] < 0)
        | (examination["Total_Marks"] > 100)
    ).any():
        reconciliation_errors["examination_range"] = int(
            (
                (examination["Internal_Marks"] < 0)
                | (examination["Internal_Marks"] > 40)
                | (examination["External_Marks"] < 0)
                | (examination["External_Marks"] > 60)
                | (examination["Total_Marks"] < 0)
                | (examination["Total_Marks"] > 100)
            ).sum()
        )
    if (
        (fees["Total_Fees"] < 0)
        | (fees["Paid_Amount"] < 0)
        | (fees["Pending_Amount"] < 0)
    ).any():
        reconciliation_errors["fee_range"] = int(
            (
                (fees["Total_Fees"] < 0)
                | (fees["Paid_Amount"] < 0)
                | (fees["Pending_Amount"] < 0)
            ).sum()
        )
    return DataQuality(
        row_counts={name: len(frame) for name, frame in frames.items()},
        missing_values={
            name: {column: int(value) for column, value in frame.isna().sum().items()}
            for name, frame in frames.items()
        },
        duplicate_student_ids=int(students["Enrollment_No"].duplicated().sum()),
        invalid_references=invalid_references,
        reconciliation_errors=reconciliation_errors,
    )


def _validate_quality(quality: DataQuality) -> None:
    required_missing = {
        dataset: {
            column: count
            for column, count in missing.items()
            if count and column in REQUIRED_COLUMNS[dataset]
        }
        for dataset, missing in quality.missing_values.items()
    }
    required_missing = {dataset: values for dataset, values in required_missing.items() if values}
    if required_missing:
        raise DataValidationError(f"Required values are missing: {required_missing}")
    if quality.duplicate_student_ids:
        raise DataValidationError("students contains duplicate Enrollment_No values")
    invalid = {name: count for name, count in quality.invalid_references.items() if count}
    if invalid:
        raise DataValidationError(f"Invalid Enrollment_No references: {invalid}")
    reconciliation = {
        name: count for name, count in quality.reconciliation_errors.items() if count
    }
    if reconciliation:
        raise DataValidationError(f"Reconciliation checks failed: {reconciliation}")


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [_record(row) for _, row in frame.iterrows()]


def _record(row: pd.Series) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.to_dict().items():
        if pd.isna(value):
            result[key] = None
        elif hasattr(value, "item"):
            result[key] = value.item()
        else:
            result[key] = value
    return result


def _rounded_mean(values: pd.Series) -> float:
    return round(float(values.mean()), 1) if not values.empty else 0.0
