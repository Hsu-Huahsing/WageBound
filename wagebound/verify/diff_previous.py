# -*- coding: utf-8 -*-
"""
wagebound.verify.diff_previous
==============================

用途：
    - 專門用來做「這一期 df」對「上一期 df」的差異比對。
    - 不自己實作任何比對邏輯，只負責：
        1) 幫你決定 VerifyConfig（key / numeric / date / 誤差）。
        2) 呼叫 verify_dataframes(expected=previous, actual=current)。
        3) 視需要把 VerifyResult 包成 dict，方便後續寫報表或丟進 runner。

設計原則：
    - 這個模組是 verify 的「薄薄一層」，所有重活都交給 verify_dataframes。
    - 你在別的地方如果已經有 VerifyConfig，就可以直接呼叫 verify_dataframes；
      diff_previous 只是幫你偷懶，不會鎖死設計。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

import pandas as pd

from . import VerifyConfig, VerifyResult, verify_dataframes


# ---------------------------------------------------------------------------
# 工具：自動推斷 numeric_cols
# ---------------------------------------------------------------------------

def _infer_numeric_cols(
    previous: pd.DataFrame,
    current: pd.DataFrame,
    key_cols: Sequence[str],
    date_cols: Optional[Sequence[str]] = None,
) -> List[str]:
    """
    從 previous / current 的欄位交集裡，自動挑出「數值欄位」當作 numeric_cols。

    規則：
        - 只看兩邊都有的欄位。
        - 排除 key_cols 與 date_cols。
        - 至少一邊是數值型別（pandas 的 numeric dtype）才納入。
    """
    date_cols = list(date_cols or [])
    common_cols = set(previous.columns) & set(current.columns)
    ignore = set(key_cols) | set(date_cols)

    candidates = [c for c in common_cols if c not in ignore]

    num_cols: List[str] = []
    for c in candidates:
        prev_is_num = pd.api.types.is_numeric_dtype(previous[c])
        curr_is_num = pd.api.types.is_numeric_dtype(current[c])
        if prev_is_num or curr_is_num:
            num_cols.append(c)

    return num_cols


# ---------------------------------------------------------------------------
# 核心對外介面：直接拿 VerifyResult
# ---------------------------------------------------------------------------

def diff_previous(
    previous: pd.DataFrame,
    current: pd.DataFrame,
    *,
    key_cols: Sequence[str],
    numeric_cols: Optional[Sequence[str]] = None,
    date_cols: Optional[Sequence[str]] = None,
    atol: float = 0.0,
    rtol: float = 0.0,
) -> VerifyResult:
    """
    比對「上一版 previous」與「目前 current」的差異，回傳 VerifyResult。

    參數
    ----
    previous :
        上一版資料（期望值，等同 verify_dataframes 的 expected）。
    current :
        目前這版資料（實際值，等同 verify_dataframes 的 actual）。
    key_cols :
        作為主鍵的欄位名稱列表，必須兩邊都存在，才有辦法比對。
    numeric_cols :
        要比對的數值欄位；
        - 若為 None，會自動從兩個 df 的欄位交集裡推斷數值欄位（排除 key / date）。
        - 若有給，就尊重你傳進來的內容。
    date_cols :
        日期欄位名稱列表（選填）。若有給，verify_dataframes 會幫你轉成 datetime。
    atol / rtol :
        數值比對的容許誤差，傳給 VerifyConfig：
            - atol: 絕對誤差
            - rtol: 相對誤差（乘在 expected 的絕對值上）
    """
    key_cols = list(key_cols)
    date_cols = list(date_cols or [])

    if numeric_cols is None:
        inferred = _infer_numeric_cols(previous, current, key_cols, date_cols)
        numeric_cols = inferred
    else:
        numeric_cols = list(numeric_cols)

    cfg = VerifyConfig(
        key_cols=key_cols,
        numeric_cols=numeric_cols,
        date_cols=date_cols or None,
        date_mode=None,  # 目前沒用到，先維持既有欄位
        atol=atol,
        rtol=rtol,
    )

    result = verify_dataframes(
        expected=previous,
        actual=current,
        config=cfg,
    )
    return result


# ---------------------------------------------------------------------------
# 工具：把 VerifyResult 包成 dict，方便報表 / runner
# ---------------------------------------------------------------------------

def diff_previous_as_dict(
    previous: pd.DataFrame,
    current: pd.DataFrame,
    *,
    name: str = "diff_previous",
    key_cols: Sequence[str],
    numeric_cols: Optional[Sequence[str]] = None,
    date_cols: Optional[Sequence[str]] = None,
    atol: float = 0.0,
    rtol: float = 0.0,
) -> Dict[str, Any]:
    """
    同 diff_previous，但回傳 dict，欄位設計成適合匯入報表或接到 runner：

        {
            "name":    <檢查名稱>,
            "passed":  <bool>,
            "level":   "info" / "warn" / "error",
            "message": <摘要字串>,
            "details": {
                "config":      <VerifyConfig>,
                "issues":      <List[VerifyIssue]>,
                "diff_rows":   <pd.DataFrame>,
            }
        }

    - passed：對應 VerifyResult.ok
    - level：
        - 若 ok=True → "info"
        - 若有 error issue → "error"
        - 否則 → "warn"
    - message：用 VerifyResult.summary()
    """
    res = diff_previous(
        previous=previous,
        current=current,
        key_cols=key_cols,
        numeric_cols=numeric_cols,
        date_cols=date_cols,
        atol=atol,
        rto
