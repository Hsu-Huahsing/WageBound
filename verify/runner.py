# -*- coding: utf-8 -*-
"""
WageBound.verify.runner
=======================

驗證流程入口函式。

特性
----
- 不依賴 command line，只設計成可以 import 的函式。
- 支援兩種入口：
    1. 已經準備好的 DataFrame → verify_dataframes()
    2. 給兩個 Excel 路徑 → verify_excels()
- 可指定：
    - key_cols：對齊用欄位
    - numeric_cols：要比對的數值欄
    - date_cols：需要轉成 datetime 的欄位（透過 StevenTricks.stringtodate）
    - 只取部分欄位做分析，避免整張超大 table 全部搬進來比
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Optional, Iterable

import pandas as pd

from .base import (
    VerifyConfig,
    VerifyResult,
    prepare_date_columns,
    compare_datasets,
)


def _ensure_list(cols: Optional[Sequence[str]]) -> list[str]:
    if cols is None:
        return []
    if isinstance(cols, str):
        return [cols]
    return list(cols)


# ----------------------------------------------------------------------
# 1. 已有 DataFrame 的情境
# ----------------------------------------------------------------------


def verify_dataframes(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    *,
    key_cols: Sequence[str],
    numeric_cols: Sequence[str],
    date_cols: Optional[Sequence[str]] = None,
    date_mode: int = 4,
    use_cols_expected: Optional[Sequence[str]] = None,
    use_cols_actual: Optional[Sequence[str]] = None,
    atol: float = 0.0,
    rtol: float = 1e-6,
) -> VerifyResult:
    """
    直接對比兩個 DataFrame。

    參數
    ----
    expected, actual : pd.DataFrame
        要比對的兩份表格。
    key_cols : Sequence[str]
        join key 欄位。
    numeric_cols : Sequence[str]
        要做數值比對的欄位。
    date_cols : Sequence[str], optional
        需要轉成 datetime 的欄位名稱（兩邊會共同處理）。
    date_mode : int
        傳給 stringtodate 的 mode，預設 4。
    use_cols_expected, use_cols_actual : Sequence[str], optional
        若有指定，只會從各自的 DataFrame 中挑選這些欄位
        （再加上 key_cols），避免整張超大 table 全部搬進來。
    atol, rtol : float
        傳給 np.isclose 的誤差設定。

    回傳
    ----
    VerifyResult
    """

    key_cols = _ensure_list(key_cols)
    numeric_cols = _ensure_list(numeric_cols)

    # 先決定要用哪些欄位
    if use_cols_expected is not None:
        cols_e = list(set(key_cols) | set(use_cols_expected))
        expected = expected.loc[:, [c for c in cols_e if c in expected.columns]].copy()
    else:
        expected = expected.copy()

    if use_cols_actual is not None:
        cols_a = list(set(key_cols) | set(use_cols_actual))
        actual = actual.loc[:, [c for c in cols_a if c in actual.columns]].copy()
    else:
        actual = actual.copy()

    # 日期欄位處理（兩邊都做）
    if date_cols:
        expected = prepare_date_columns(expected, date_cols=date_cols, mode=date_mode)
        actual = prepare_date_columns(actual, date_cols=date_cols, mode=date_mode)

    cfg = VerifyConfig(
        expected=expected,
        actual=actual,
        key_cols=list(key_cols),
        numeric_cols=list(numeric_cols),
        atol=atol,
        rtol=rtol,
    )
    return compare_datasets(cfg)


# ----------------------------------------------------------------------
# 2. 直接從 Excel 檔讀取的情境
# ----------------------------------------------------------------------


def _read_excel(
    path: Path | str,
    *,
    sheet: int | str | None = 0,
    dtype: str | dict | None = "object",
) -> pd.DataFrame:
    return pd.read_excel(Path(path), sheet_name=sheet, dtype=dtype)


def verify_excels(
    expected_path: str | Path,
    actual_path: str | Path,
    *,
    key_cols: Sequence[str],
    numeric_cols: Sequence[str],
    date_cols: Optional[Sequence[str]] = None,
    date_mode: int = 4,
    sheet_expected: int | str | None = 0,
    sheet_actual: int | str | None = 0,
    use_cols_expected: Optional[Sequence[str]] = None,
    use_cols_actual: Optional[Sequence[str]] = None,
    dtype_expected: str | dict | None = "object",
    dtype_actual: str | dict | None = "object",
    atol: float = 0.0,
    rtol: float = 1e-6,
) -> VerifyResult:
    """
    從兩個 Excel 檔讀取資料並進行驗證。

    典型用法：
    --------
    >>> from WageBound.verify.runner import verify_excels
    >>> res = verify_excels(
    ...     expected_path="data/old_version.xlsx",
    ...     actual_path="data/new_version.xlsx",
    ...     key_cols=["Case_ID"],
    ...     numeric_cols=["Funding_Amt", "Rate"],
    ...     date_cols=["Apply_Date"],
    ... )

    之後可以查看：
    >>> res.summary
    >>> res.diff_rows
    """
    expected_df = _read_excel(
        expected_path,
        sheet=sheet_expected,
        dtype=dtype_expected,
    )
    actual_df = _read_excel(
        actual_path,
        sheet=sheet_actual,
        dtype=dtype_actual,
    )

    return verify_dataframes(
        expected=expected_df,
        actual=actual_df,
        key_cols=key_cols,
        numeric_cols=numeric_cols,
        date_cols=date_cols,
        date_mode=date_mode,
        use_cols_expected=use_cols_expected,
        use_cols_actual=use_cols_actual,
        atol=atol,
        rtol=rtol,
    )


__all__ = [
    "verify_dataframes",
    "verify_excels",
]


"""
4️⃣ 怎麼用（實務範例）
情境 A：我有一張很大的明細表，但只想比幾個欄位

import pandas as pd
from WageBound.verify.runner import verify_dataframes

df_old = pd.read_parquet("huge_table_old.parquet")
df_new = pd.read_parquet("huge_table_new.parquet")

res = verify_dataframes(
    expected=df_old,
    actual=df_new,
    key_cols=["Cust_ID", "Loan_ID"],
    numeric_cols=["Funding_Amt", "DBR_after"],
    date_cols=["Apply_Date"],         # 會透過 stringtodate 轉成 datetime
    use_cols_expected=["Funding_Amt", "DBR_after", "Apply_Date"],
    use_cols_actual=["Funding_Amt", "DBR_after", "Apply_Date"],
    atol=1e-2,                        # 允許 0.01 的絕對誤差
)

print(res.summary)
print(res.diff_rows.head())
"""


"""
from WageBound.verify.diff_previous import diff_between_versions

res = diff_between_versions(
    previous_file=r"E:\report\HPM_output_202510_v1.xlsx",
    current_file=r"E:\report\HPM_output_202510_v2.xlsx",
    key_cols=["Case_ID"],
    numeric_cols=["Funding_Amt", "Total_Income"],
    date_cols=["Apply_Date"],
)

# 差異摘要
print(res.summary)

# 個別差異列另存成 Excel 方便人工檢查
res.diff_rows.to_excel(r"E:\report\HPM_diff_case_list.xlsx", index=False)

"""