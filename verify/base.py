# verify/base.py
# -*- coding: utf-8 -*-
"""
驗證框架核心：

- ValidationIssue：單筆異常紀錄
- ValidationRule：單一驗證規則（含 id/描述/檢查函式/嚴重等級）
- run_rules()    ：執行多個規則，回傳完整 issue DataFrame
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Dict, Any, Literal, Optional

import pandas as pd


Severity = Literal["error", "warning"]


@dataclass
class ValidationIssue:
    rule_id: str
    severity: Severity
    message: str
    row_idx: Optional[int] = None
    key_values: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
        }
        if self.row_idx is not None:
            d["row_idx"] = self.row_idx
        if self.key_values:
            d.update({f"key_{k}": v for k, v in self.key_values.items()})
        return d


@dataclass
class ValidationRule:
    """
    一條驗證規則：
    - id：規則代碼（例如 'SCHEMA_001'）
    - description：中文描述
    - severity：錯誤等級（error / warning）
    - check_fn：實際執行檢查的函式：
        check_fn(df) -> List[ValidationIssue]
    """
    id: str
    description: str
    severity: Severity
    check_fn: Callable[[pd.DataFrame], List[ValidationIssue]]

    def run(self, df: pd.DataFrame) -> List[ValidationIssue]:
        issues = self.check_fn(df) or []
        # 強制填 rule_id / severity
        for iss in issues:
            iss.rule_id = self.id
            iss.severity = self.severity
        return issues


def run_rules(df: pd.DataFrame, rules: List[ValidationRule]) -> pd.DataFrame:
    """
    依序執行多條規則，把全部異常合併成一個 DataFrame。
    """
    all_issues: List[ValidationIssue] = []
    for rule in rules:
        res = rule.run(df)
        all_issues.extend(res)

    if not all_issues:
        return pd.DataFrame(columns=["rule_id", "severity", "message", "row_idx"])

    return pd.DataFrame([x.to_dict() for x in all_issues])
