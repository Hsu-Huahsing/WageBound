# -*- coding: utf-8 -*-
"""
WageBound.verify.base
=====================

通用驗證核心模組。

設計目標
--------
- 不綁特定專案（HPM、薪轉、DBR 都可以用）
- 不依賴 CLI，只要 import 就能在 .py / Notebook 直接呼叫
- 把「對比兩份表格」這件事收斂成固定流程：
    1. 指定 key 欄位（join key）
    2. 指定要對比的數值欄位
    3. 自動產出差異列與摘要
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Optional

import numpy as np
import pandas as pd

try:
    # 你自己的工具箱，若沒有就單純略過日期處理
    from StevenTricks.convert_utils import stringtodate
except ImportError:  # pragma: no cover
    stringtodate = None  # type: ignore[assignment]


# ----------------------------------------------------------------------
# Dataclasses：設定與結果結構
# ----------------------------------------------------------------------


@dataclass
class VerifyConfig:
    """
    驗證設定

    Attributes
    ----------
    expected : pd.DataFrame
        「舊版本 / 標準答案」的資料表。
    actual : pd.DataFrame
        「新版本 / 被驗證對象」的資料表。
    key_cols : list[str]
        join 用的 key 欄位（例如 ['Case_ID', 'Proj_ID']）。
    numeric_cols : list[str]
        要做數值比對的欄位（例如 ['Funding_Amt', 'Rate']）。
    label_expected : str
        merge 後 expected 欄位的 suffix。
    label_actual : str
        merge 後 actual 欄位的 suffix。
    atol : float
        絕對誤差容忍度。
    rtol : float
        相對誤差容忍度。
    """

    expected: pd.DataFrame
    actual: pd.DataFrame
    key_cols: List[str]
    numeric_cols: List[str]
    label_expected: str = "exp"
    label_actual: str = "act"
    atol: float = 0.0
    rtol: float = 1e-6


@dataclass
class VerifyResult:
    """
    驗證結果物件

    Attributes
    ----------
    merged : pd.DataFrame
        expected / actual merge 後的完整結果（含 _merge、各欄位 suffix）。
    diff_rows : pd.DataFrame
        在 numeric_cols 任一欄有差異的列。
    missing_in_expected : pd.DataFrame
        只出現在 actual、不在 expected 的 key。
    missing_in_actual : pd.DataFrame
        只出現在 expected、不在 actual 的 key。
    summary : pd.DataFrame
        各數值欄位的差異摘要（筆數、最大/平均絕對差）。
    """

    merged: pd.DataFrame
    diff_rows: pd.DataFrame
    missing_in_expected: pd.DataFrame
    missing_in_actual: pd.DataFrame
    summary: pd.DataFrame


# ----------------------------------------------------------------------
# 工具函式
# ----------------------------------------------------------------------


def ensure_list(cols: Optional[Sequence[str]]) -> List[str]:
    """把 None / 單一字串 統一轉成 list[str]。"""
    if cols is None:
        return []
    if isinstance(cols, str):
        return [cols]
    return list(cols)


def prepare_date_columns(
    df: pd.DataFrame,
    date_cols: Sequence[str],
    mode: int = 4,
) -> pd.DataFrame:
    """
    使用你的 StevenTricks.stringtodate 將指定欄位轉成 datetime64[ns]。

    如果 stringtodate 不存在（例如在公司外部環境），這個函式會安靜略過。

    參數
    ----
    df : pd.DataFrame
        原始 DataFrame。
    date_cols : Sequence[str]
        需要轉日期的欄位名稱。
    mode : int
        傳給 stringtodate 的 mode，預設 4（你原本 ROC 壓縮格式）。

    回傳
    ----
    pd.DataFrame
        同一個 df 物件（就地修改），但指定欄位已轉為 datetime。
    """
    cols = [c for c in ensure_list(date_cols) if c in df.columns]
    if not cols or stringtodate is None:
        return df

    # 你自己的工具：會 in-place 更新 df[cols]
    stringtodate(df, datecol=cols, mode=mode)
    return df


# ----------------------------------------------------------------------
# 核心：兩份 DataFrame 的比對邏輯
# ----------------------------------------------------------------------


def _merge_expected_actual(cfg: VerifyConfig) -> pd.DataFrame:
    """依 key_cols 將 expected / actual merge 起來。"""
    left = cfg.expected.copy()
    right = cfg.actual.copy()

    # 確認 key 欄位都有
    for col in cfg.key_cols:
        if col not in left.columns:
            raise KeyError(f"expected 缺少 key 欄位：{col!r}")
        if col not in right.columns:
            raise KeyError(f"actual 缺少 key 欄位：{col!r}")

    merged = left.merge(
        right,
        on=cfg.key_cols,
        how="outer",
        suffixes=(f"_{cfg.label_expected}", f"_{cfg.label_actual}"),
        indicator=True,
    )
    return merged


def compare_datasets(cfg: VerifyConfig) -> VerifyResult:
    """
    依照 VerifyConfig 對比 expected / actual 兩份資料。

    流程
    ----
    1. 依 key_cols 做 outer merge。
    2. 抓出只在 expected / 只在 actual 的 key。
    3. 對 numeric_cols 做誤差判定（np.isclose with atol / rtol）。
    4. 產生 diff_rows 與 summary。

    回傳
    ----
    VerifyResult
        包含 merged / diff_rows / 缺漏列 / 摘要。
    """
    merged = _merge_expected_actual(cfg)

    # 缺失列
    missing_in_expected = merged[merged["_merge"] == "right_only"].copy()
    missing_in_actual = merged[merged["_merge"] == "left_only"].copy()

    both = merged[merged["_merge"] == "both"].copy()
    if both.empty:
        # 完全沒有 key 對上，直接回空結果
        empty_summary = pd.DataFrame(
            columns=["col", "n_diff_rows", "max_abs_diff", "mean_abs_diff"]
        )
        return VerifyResult(
            merged=merged,
            diff_rows=both,
            missing_in_expected=missing_in_expected,
            missing_in_actual=missing_in_actual,
            summary=empty_summary,
        )

    diff_mask = np.zeros(len(both), dtype=bool)
    col_pairs = []

    for col in cfg.numeric_cols:
        col_exp = f"{col}_{cfg.label_expected}"
        col_act = f"{col}_{cfg.label_actual}"
        if col_exp not in both.columns or col_act not in both.columns:
            # 這種情況通常是欄位少建 / 欄位名對不起來，讓使用者自己處理
            continue

        # 轉 float 做誤差比對；無法轉換的視為 NaN，由 np.isclose(equal_nan=True) 處理
        left_vals = pd.to_numeric(both[col_exp], errors="coerce")
        right_vals = pd.to_numeric(both[col_act], errors="coerce")

        is_close = np.isclose(
            left_vals.to_numpy(dtype="float64"),
            right_vals.to_numpy(dtype="float64"),
            rtol=cfg.rtol,
            atol=cfg.atol,
            equal_nan=True,
        )
        diff = ~is_close
        diff_mask |= diff
        col_pairs.append((col, col_exp, col_act))

    diff_rows = both.loc[diff_mask].copy()

    # 建摘要表
    rows = []
    for col, col_exp, col_act in col_pairs:
        if diff_rows.empty:
            cnt = 0
            max_abs = 0.0
            mean_abs = 0.0
        else:
            lv = pd.to_numeric(diff_rows[col_exp], errors="coerce")
            rv = pd.to_numeric(diff_rows[col_act], errors="coerce")
            diff_val = (rv - lv).to_numpy(dtype="float64")
            valid = ~np.isnan(diff_val)

            if not valid.any():
                cnt = 0
                max_abs = 0.0
                mean_abs = 0.0
            else:
                diff_non_nan = diff_val[valid]
                cnt = int((diff_non_nan != 0).sum())
                max_abs = float(np.max(np.abs(diff_non_nan))) if cnt else 0.0
                mean_abs = float(np.mean(np.abs(diff_non_nan))) if cnt else 0.0

        rows.append(
            {
                "col": col,
                "n_diff_rows": cnt,
                "max_abs_diff": max_abs,
                "mean_abs_diff": mean_abs,
            }
        )

    summary = pd.DataFrame(rows)

    return VerifyResult(
        merged=merged,
        diff_rows=diff_rows,
        missing_in_expected=missing_in_expected,
        missing_in_actual=missing_in_actual,
        summary=summary,
    )


__all__ = [
    "VerifyConfig",
    "VerifyResult",
    "prepare_date_columns",
    "compare_datasets",
]
