# -*- coding: utf-8 -*-
"""
WageBound.verify 封裝

統一對外匯出：

- expected vs actual 比對核心：
    - VerifyConfig / VerifyIssue / VerifyResult / verify_dataframes

- 規則式檢查：
    - ValidationRule / ValidationIssue
    - rules.* 工廠函式

- 檢查註冊與批次執行：
    - VERIFIER_REGISTRY / register
    - list_available_checks / run_verifications
"""

from .base import (
    VerifyConfig,
    VerifyIssue,
    VerifyResult,
    verify_dataframes,
    ValidationIssue,
    ValidationRule,
    VERIFIER_REGISTRY,
    register,
)
from .runner import list_available_checks, run_verifications
from . import rules

__all__ = [
    # expected vs actual
    "VerifyConfig",
    "VerifyIssue",
    "VerifyResult",
    "verify_dataframes",
    # 規則式檢查
    "ValidationIssue",
    "ValidationRule",
    "rules",
    # registry / runner
    "VERIFIER_REGISTRY",
    "register",
    "list_available_checks",
    "run_verifications",
]
