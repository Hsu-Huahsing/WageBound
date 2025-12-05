# -*- coding: utf-8 -*-
"""
wagebound.verify.rules
======================

結構 / 欄位 / 型別 / 範圍類驗證規則的工廠函式。

這個模組只負責「幫你組 ValidationRule」，
實際執行則交給 ValidationRule.run(df)。
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd

from .base import ValidationIssue, ValidationRule


def make_required_columns_rule(required_cols: List[str]) -> ValidationRule:
    """
    檢查指定欄位是否全部存在。
    """

    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col in required_cols:
            if col not in df.columns:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        rule_id="SCHEMA_REQUIRED_COLUMNS",
                        message=f"缺少必要欄位：{col}",
                        column=col,
                        row_idx=None,
                        key_values={},
                    )
                )
        return issues

    return ValidationRule(
        id="SCHEMA_REQUIRED_COLUMNS",
        description="檢查必要欄位是否存在",
        severity="error",
        check_fn=_check,
    )


def make_dtype_rule(expected_dtypes: Dict[str, str]) -> ValidationRule:
    """
    檢查欄位 dtype 是否符合預期。

    expected_dtypes:
        - key   : 欄位名稱
        - value : 預期 dtype 字串（例如 'int64', 'float64', 'object', 'datetime64[ns]'）
    """

    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col, expected_dtype in expected_dtypes.items():
            if col not in df.columns:
                # 交給 required_columns_rule 處理，這裡略過
                continue
            actual_dtype = str(df[col].dtype)
            if actual_dtype != expected_dtype:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        rule_id="SCHEMA_DTYPE_MISMATCH",
                        message=f"欄位 {col} dtype 不符，預期 {expected_dtype}，實際 {actual_dtype}",
                        column=col,
                        row_idx=None,
                        key_values={"expected_dtype": expected_dtype, "actual_dtype": actual_dtype},
                    )
                )
        return issues

    return ValidationRule(
        id="SCHEMA_DTYPE_MISMATCH",
        description="檢查欄位 dtype 是否符合預期",
        severity="error",
        check_fn=_check,
    )


def make_notnull_rule(required_notnull_cols: List[str]) -> ValidationRule:
    """
    檢查某些欄位是否存在缺值。
    """

    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col in required_notnull_cols:
            if col not in df.columns:
                # 交給 required_columns_rule 處理，這裡略過
                continue
            null_idx = df.index[df[col].isna()]
            for idx in null_idx:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        rule_id="SCHEMA_NOTNULL",
                        message=f"欄位 {col} 不應為空值，但在列 {idx} 發現缺值。",
                        column=col,
                        row_idx=int(idx) if isinstance(idx, (int, float)) else None,
                        key_values={"column": col},
                    )
                )
        return issues

    return ValidationRule(
        id="SCHEMA_NOTNULL",
        description="檢查欄位是否為 NOT NULL",
        severity="error",
        check_fn=_check,
    )


def make_numeric_range_rule(
    numeric_ranges: Dict[str, Tuple[Optional[float], Optional[float]]]
) -> ValidationRule:
    """
    檢查數值欄位是否落在合理範圍內。

    numeric_ranges:
        - key   : 欄位名稱
        - value : (lower, upper)，允許其中之一為 None 代表「只檢查上限或下限」。
    """

    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col, (lower, upper) in numeric_ranges.items():
            if col not in df.columns:
                continue

            series = pd.to_numeric(df[col], errors="coerce")
            mask = pd.Series(True, index=series.index)

            if lower is not None:
                mask &= series >= lower
            if upper is not None:
                mask &= series <= upper

            # 取出超出範圍的列
            bad_idx = series.index[~mask]
            for idx in bad_idx:
                val = series.loc[idx]
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        rule_id="SCHEMA_NUMERIC_RANGE",
                        message=f"欄位 {col} 數值超出合理範圍 [{lower}, {upper}]，實際值={val}",
                        column=col,
                        row_idx=int(idx) if isinstance(idx, (int, float)) else None,
                        key_values={"column": col, "value": val},
                    )
                )

        return issues

    return ValidationRule(
        id="SCHEMA_NUMERIC_RANGE",
        description="檢查數值欄位是否落在合理範圍內",
        severity="warning",
        check_fn=_check,
    )


__all__ = [
    "make_required_columns_rule",
    "make_dtype_rule",
    "make_notnull_rule",
    "make_numeric_range_rule",
]
