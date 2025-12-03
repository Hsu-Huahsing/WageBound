# -*- coding: utf-8 -*-
"""
WageBound.verify.diff_previous
==============================

用來比對「前一版輸出」與「最新輸出」的差異。

本質上只是呼叫 verify.runner.verify_excels()，
只是把語意說清楚，讓未來在 Notebook / Script 裡面閱讀起來比較直覺。
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Optional

from .runner import verify_excels
from .base import VerifyResult


def diff_between_versions(
    previous_file: str | Path,
    current_file: str | Path,
    *,
    key_cols: Sequence[str],
    numeric_cols: Sequence[str],
    date_cols: Optional[Sequence[str]] = None,
    date_mode: int = 4,
    sheet_previous: int | str | None = 0,
    sheet_current: int | str | None = 0,
) -> VerifyResult:
    """
    比對「前一版 vs 最新版」的 Excel 結果。

    參數
    ----
    previous_file : str | Path
        舊版結果檔（當成 expected）。
    current_file : str | Path
        新版結果檔（當成 actual）。
    key_cols : Sequence[str]
        join key。
    numeric_cols : Sequence[str]
        要比對的數值欄位。
    date_cols : Sequence[str], optional
        若有的話，會用同樣的規則先轉成 datetime。
    date_mode : int
        傳給 stringtodate 的 mode，預設 4。
    sheet_previous, sheet_current : int | str | None
        各自的工作表名稱或 index。

    回傳
    ----
    VerifyResult
    """
    return verify_excels(
        expected_path=previous_file,
        actual_path=current_file,
        key_cols=key_cols,
        numeric_cols=numeric_cols,
        date_cols=date_cols,
        date_mode=date_mode,
        sheet_expected=sheet_previous,
        sheet_actual=sheet_current,
    )


__all__ = [
    "diff_between_versions",
]
