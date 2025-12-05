# -*- coding: utf-8 -*-
"""
wagebound.verify.rules
======================

用途：
    - 統一放「欄位 / 型別 / 範圍 / 唯一性」這類規則式驗證的工廠函式。
    - 每個工廠回傳一個 ValidationRule，實際檢查邏輯由 rule.run(df) 執行。
    - 不做 I/O、不 print，只回傳結構化的 ValidationIssue。

典型用法：
    from wagebound.verify.rules import (
        make_required_columns_rule,
        make_dtype_rule,
        make_notnull_rule,
        make_numeric_range_rule,
        make_unique_key_rule,
        run_rules,
        issues_to_dataframe,
    )

    rules = [
        make_required_columns_rule([...]),
        make_dtype_rule({...}),
        make_notnull_rule([...]),
        make_numeric_range_rule({...}),
        make_unique_key_rule([...]),
    ]

    issues = run_rules(df, rules)
    issues_df = issues_to_dataframe(issues)
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd

from .base import ValidationIssue, ValidationRule


# ---------------------------------------------------------------------------
# 規則工廠：必要欄位
# ---------------------------------------------------------------------------


def make_required_columns_rule(
    required_cols: Sequence[str],
    *,
    rule_id: str = "SCHEMA_REQUIRED_COLUMNS",
    severity: str = "error",
    description: Optional[str] = None,
) -> ValidationRule:
    """
    檢查指定欄位是否全部存在。

    required_cols
        - 必須存在於 df.columns 的欄位名稱列表。
    """

    required_cols = list(required_cols)
    if description is None:
        description = f"檢查必要欄位是否存在：{', '.join(required_cols)}"

    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for col in required_cols:
            if col not in df.columns:
                issues.append(
                    ValidationIssue(
                        severity=severity,
                        rule_id=rule_id,
                        message=f"缺少必要欄位：{col}",
                        column=col,
                        row_idx=None,
                        key_values={},
                    )
                )
        return issues

    return ValidationRule(
        id=rule_id,
        description=description,
        severity=severity,
        check_fn=_check,
    )


# ---------------------------------------------------------------------------
# 規則工廠：dtype 檢查
# ---------------------------------------------------------------------------


def make_dtype_rule(
    expected_dtypes: Mapping[str, str],
    *,
    rule_id: str = "SCHEMA_DTYPE_MISMATCH",
    severity: str = "error",
    description: Optional[str] = None,
) -> ValidationRule:
    """
    檢查欄位 dtype 是否符合預期。

    expected_dtypes:
        - key   : 欄位名稱
        - value : 預期 dtype 字串（例如 'int64', 'float64', 'object', 'datetime64[ns]'）

    注意：
        - 若欄位不存在，這條 rule 不會報錯，留給 required_columns_rule 處理。
    """

    expected_dtypes = dict(expected_dtypes)
    if description is None:
        description = "檢查欄位 dtype 是否符合預期"

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
                        severity=severity,
                        rule_id=rule_id,
                        message=(
                            f"欄位 {col} dtype 不符，"
                            f"預期 {expected_dtype}，實際 {actual_dtype}"
                        ),
                        column=col,
                        row_idx=None,
                        key_values={
                            "expected_dtype": expected_dtype,
                            "actual_dtype": actual_dtype,
                        },
                    )
                )
        return issues

    return ValidationRule(
        id=rule_id,
        description=description,
        severity=severity,
        check_fn=_check,
    )


# ---------------------------------------------------------------------------
# 規則工廠：NOT NULL 檢查
# ---------------------------------------------------------------------------


def make_notnull_rule(
    required_notnull_cols: Sequence[str],
    *,
    rule_id: str = "SCHEMA_NOTNULL",
    severity: str = "error",
    description: Optional[str] = None,
) -> ValidationRule:
    """
    檢查某些欄位是否存在缺值（NaN / None）。

    required_notnull_cols
        - 要求「不得為空值」的欄位名稱列表。
    """

    required_notnull_cols = list(required_notnull_cols)
    if description is None:
        description = f"檢查欄位不得為空值：{', '.join(required_notnull_cols)}"

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
                        severity=severity,
                        rule_id=rule_id,
                        message=f"欄位 {col} 不應為空值，但在列 {idx} 發現缺值。",
                        column=col,
                        row_idx=int(idx) if isinstance(idx, (int, float)) else None,
                        key_values={"column": col},
                    )
                )
        return issues

    return ValidationRule(
        id=rule_id,
        description=description,
        severity=severity,
        check_fn=_check,
    )


# ---------------------------------------------------------------------------
# 規則工廠：數值範圍檢查
# ---------------------------------------------------------------------------


def make_numeric_range_rule(
    numeric_ranges: Mapping[str, Tuple[Optional[float], Optional[float]]],
    *,
    rule_id: str = "SCHEMA_NUMERIC_RANGE",
    severity: str = "warning",
    description: Optional[str] = None,
) -> ValidationRule:
    """
    檢查數值欄位是否落在合理範圍內。

    numeric_ranges:
        - key   : 欄位名稱
        - value : (lower, upper)，允許其中之一為 None 代表「只檢查上限或下限」。

    例如：
        numeric_ranges = {
            "AGE": (18, 120),
            "LTV": (0.0, 2.0),
        }
    """

    numeric_ranges = dict(numeric_ranges)
    if description is None:
        description = "檢查數值欄位是否落在合理範圍內"

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
                        severity=severity,
                        rule_id=rule_id,
                        message=(
                            f"欄位 {col} 數值超出合理範圍 "
                            f"[{lower}, {upper}]，實際值={val}"
                        ),
                        column=col,
                        row_idx=int(idx) if isinstance(idx, (int, float)) else None,
                        key_values={"column": col, "value": val},
                    )
                )

        return issues

    return ValidationRule(
        id=rule_id,
        description=description,
        severity=severity,
        check_fn=_check,
    )


# ---------------------------------------------------------------------------
# 規則工廠：唯一鍵檢查（duplicated key）
# ---------------------------------------------------------------------------


def make_unique_key_rule(
    key_cols: Sequence[str],
    *,
    rule_id: str = "SCHEMA_UNIQUE_KEY",
    severity: str = "error",
    description: Optional[str] = None,
) -> ValidationRule:
    """
    檢查指定 key_cols 組成的鍵是否在資料中唯一。

    典型用法：
        - key_cols = ["Cust_ID"]
        - key_cols = ["Cust_ID", "AsOfDate"]
    """

    key_cols = list(key_cols)
    if description is None:
        description = f"檢查鍵唯一性：{', '.join(key_cols)}"

    def _check(df: pd.DataFrame) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        for col in key_cols:
            if col not in df.columns:
                # 若 key 欄位本身不存在，交給 required_columns_rule 處理
                return issues

        dup_mask = df.duplicated(subset=key_cols, keep=False)
        dup_idx = df.index[dup_mask]

        for idx in dup_idx:
            row = df.loc[idx]
            key_values = {col: row[col] for col in key_cols}
            issues.append(
                ValidationIssue(
                    severity=severity,
                    rule_id=rule_id,
                    message=(
                        f"鍵 {key_values} 非唯一，"
                        f"key_cols={key_cols}"
                    ),
                    column=None,
                    row_idx=int(idx) if isinstance(idx, (int, float)) else None,
                    key_values=key_values,
                )
            )

        return issues

    return ValidationRule(
        id=rule_id,
        description=description,
        severity=severity,
        check_fn=_check,
    )


# ---------------------------------------------------------------------------
# 工具：一次跑多條規則 + 轉成 DataFrame
# ---------------------------------------------------------------------------


def run_rules(df: pd.DataFrame, rules: Iterable[ValidationRule]) -> List[ValidationIssue]:
    """
    依序執行多條 ValidationRule，回傳所有 issue 的列表。

    - 不會去重複 issue；
    - 規則之間互不影響。
    """
    issues: List[ValidationIssue] = []
    for rule in rules:
        rule_issues = rule.run(df)
        # 保守一點：確保每個 issue 的 rule_id / severity 至少有預設值
        for iss in rule_issues:
            if not iss.rule_id:
                iss.rule_id = rule.id
            if not iss.severity:
                iss.severity = rule.severity
        issues.extend(rule_issues)
    return issues


def issues_to_dataframe(issues: Sequence[ValidationIssue]) -> pd.DataFrame:
    """
    將 ValidationIssue 列表攤平成 DataFrame，方便後續寫入 Excel / DB。

    欄位大致為：
        - severity
        - rule_id
        - message
        - column
        - row_idx
        - 以及 key_values 攤平後的欄位（若有）。
    """
    if not issues:
        return pd.DataFrame(
            columns=["severity", "rule_id", "message", "column", "row_idx"]
        )

    rows: List[Dict[str, object]] = []
    for iss in issues:
        base_row: Dict[str, object] = {
            "severity": iss.severity,
            "rule_id": iss.rule_id,
            "message": iss.message,
            "column": iss.column,
            "row_idx": iss.row_idx,
        }
        # 把 key_values 攤平，避免塞在一個 dict 欄位裡不好 filter
        for k, v in (iss.key_values or {}).items():
            key = f"key_{k}"
            if key not in base_row:
                base_row[key] = v
        rows.append(base_row)

    return pd.DataFrame(rows)


__all__ = [
    "make_required_columns_rule",
    "make_dtype_rule",
    "make_notnull_rule",
    "make_numeric_range_rule",
    "make_unique_key_rule",
    "run_rules",
    "issues_to_dataframe",
]
