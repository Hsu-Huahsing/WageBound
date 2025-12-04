# verify/rules.py
# -*- coding: utf-8 -*-
"""
結構 / 欄位 / 型別 / 範圍類驗證規則
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd

from .base import ValidationRule, ValidationIssue


def make_required_columns_rule(required_cols: List[str]) -> ValidationRule:
    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            issues.append(
                ValidationIssue(
                    rule_id="SCHEMA_REQUIRED_COLS",
                    severity="error",
                    message=f"缺少必要欄位：{', '.join(missing)}",
                )
            )
        return issues

    return ValidationRule(
        id="SCHEMA_REQUIRED_COLS",
        description=f"檢查必要欄位是否存在：{', '.join(required_cols)}",
        severity="error",
        check_fn=_check,
    )


def make_dtype_rule(expected_dtypes: Dict[str, str]) -> ValidationRule:
    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col, expect in expected_dtypes.items():
            if col not in df.columns:
                continue
            actual = str(df[col].dtype)
            if actual != expect:
                issues.append(
                    ValidationIssue(
                        rule_id="SCHEMA_DTYPE_MISMATCH",
                        severity="error",
                        message=f"欄位 {col} 型別不符：預期 {expect}，實際 {actual}",
                    )
                )
        return issues

    return ValidationRule(
        id="SCHEMA_DTYPE_MISMATCH",
        description="檢查欄位 dtype 是否符合預期",
        severity="error",
        check_fn=_check,
    )


def make_notnull_rule(
    required_notnull_cols: List[str],
) -> ValidationRule:
    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col in required_notnull_cols:
            if col not in df.columns:
                continue
            na_idx = df.index[df[col].isna()]
            for idx in na_idx:
                issues.append(
                    ValidationIssue(
                        rule_id="SCHEMA_NOTNULL",
                        severity="error",
                        message=f"欄位 {col} 不可為空值",
                        row_idx=int(idx),
                        key_values={"column": col},
                    )
                )
        return issues

    return ValidationRule(
        id="SCHEMA_NOTNULL",
        description=f"檢查欄位不得為空：{', '.join(required_notnull_cols)}",
        severity="error",
        check_fn=_check,
    )


def make_numeric_range_rule(
    ranges: Dict[str, Tuple[Optional[float], Optional[float]]]
) -> ValidationRule:
    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col, (lower, upper) in ranges.items():
            if col not in df.columns:
                continue
            series = pd.to_numeric(df[col], errors="coerce")
            mask = pd.Series(False, index=df.index)
            if lower is not None:
                mask |= series < lower
            if upper is not None:
                mask |= series > upper
            bad_idx = df.index[mask.fillna(False)]
            for idx in bad_idx:
                val = df.at[idx, col]
                issues.append(
                    ValidationIssue(
                        rule_id="SCHEMA_NUMERIC_RANGE",
                        severity="warning",
                        message=f"欄位 {col} 數值超出合理範圍 [{lower}, {upper}]，實際值={val}",
                        row_idx=int(idx),
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
