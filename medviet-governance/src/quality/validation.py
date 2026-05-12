# src/quality/validation.py
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
import re
from great_expectations.expectations import (
    ExpectColumnValueLengthsToEqual,
    ExpectColumnValuesToBeBetween,
    ExpectColumnValuesToBeInSet,
    ExpectColumnValuesToBeUnique,
    ExpectColumnValuesToMatchRegex,
    ExpectColumnValuesToNotBeNull,
)

def build_patient_expectation_suite() -> ExpectationSuite:
    """
    Tạo expectation suite cho patient data.
    """
    context = gx.get_context()
    suite = ExpectationSuite(name="patient_data_suite")
    suite = context.suites.add_or_update(suite)

    valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
    suite.expectations = []
    suite.add_expectation(ExpectColumnValuesToNotBeNull(column="patient_id"))
    suite.add_expectation(ExpectColumnValueLengthsToEqual(column="cccd", value=12))
    suite.add_expectation(
        ExpectColumnValuesToBeBetween(
            column="ket_qua_xet_nghiem",
            min_value=0,
            max_value=50,
        )
    )
    suite.add_expectation(
        ExpectColumnValuesToBeInSet(column="benh", value_set=valid_conditions)
    )
    suite.add_expectation(
        ExpectColumnValuesToMatchRegex(
            column="email",
            regex=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        )
    )
    suite.add_expectation(ExpectColumnValuesToBeUnique(column="patient_id"))
    context.suites.add_or_update(suite)
    return suite


def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    original_df = pd.read_csv("data/raw/patients_raw.csv")
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    original_cccds = set(original_df["cccd"].astype(str))
    reused_cccds = df["cccd"].astype(str).isin(original_cccds)
    if reused_cccds.any():
        results["success"] = False
        results["failed_checks"].append(
            "Anonymized dataset vẫn chứa CCCD gốc từ raw dataset."
        )

    required_columns = ["patient_id", "ho_ten", "cccd", "so_dien_thoai", "email"]
    null_columns = [column for column in required_columns if df[column].isnull().any()]
    if null_columns:
        results["success"] = False
        results["failed_checks"].append(
            f"Các cột quan trọng có giá trị null: {', '.join(null_columns)}"
        )

    if len(df) != len(original_df):
        results["success"] = False
        results["failed_checks"].append(
            "Số dòng anonymized data không khớp raw data."
        )

    email_pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    invalid_emails = ~df["email"].astype(str).str.match(email_pattern)
    if invalid_emails.any():
        results["success"] = False
        results["failed_checks"].append(
            "Anonymized dataset có email không đúng định dạng."
        )

    results["stats"]["pii_columns_validated"] = required_columns
    results["stats"]["row_count_matches"] = len(df) == len(original_df)
    results["stats"]["raw_cccd_leak_count"] = int(reused_cccds.sum())

    return results
