# -*- coding: utf-8 -*-
"""
verify/base.py

HPM 驗證共用工具：
1) 載入測試 Excel
2) （可選）日期欄位轉成 datetime
3) 呼叫 HPM API 取得結果
4) 依 key + 欄位 mapping 做差異比對
5) 輸出 diff 結果
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Sequence, Tuple

import pandas as pd
import requests

# 專案內部設定
from config.verify_config import (
    HPM_TEST_XLSX,
    HPM_API_URL,
    HPM_OUTPUT_DIR,
    HPM_HISTORY_DIR,
    HPM_COMPARE_COLS,
)

# 你自己的日期轉換工具（在 StevenTricks 裡）
from StevenTricks.convert_utils import stringtodate


@dataclass
class VerifyCaseConfig:
    """
    一個「驗證情境」的設定：
      - name: case 名稱，用來命名輸出檔
      - sheet_name: 測試 Excel 的分頁
      - key_cols: 用來對齊匯入 vs API 的 key 欄位
      - compare_cols: 要比對的欄位 mapping（匯入欄名 → API 欄名）
      - date_cols: 需要轉成 datetime 的欄位（匯入端）
      - use_cols: 匯入端真的需要的欄位（可選擇性縮小）
    """
    name: str
    sheet_name: str
    key_cols: List[str]
    compare_cols: Dict[str, str]
    date_cols: Optional[List[str]] = None
    use_cols: Optional[List[str]] = None


# ----------------------------------------------------------------------
# 1. 載入測試資料 + 日期欄位處理 + 欄位篩選
# ----------------------------------------------------------------------
def load_hpm_cases(
    cfg: VerifyCaseConfig,
    xlsx_path: Path | str = HPM_TEST_XLSX,
) -> pd.DataFrame:
    """
    從 Excel 載入 HPM 測試個案，並依設定做：
      - 只留 use_cols
      - 選擇性將 date_cols 轉成 datetime64[ns]
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"HPM 測試檔不存在：{xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name=cfg.sheet_name)

    # 只保留需要的欄位（如果有指定）
    if cfg.use_cols:
        missing = [c for c in cfg.use_cols if c not in df.columns]
        if missing:
            raise ValueError(f"測試檔缺少必要欄位：{missing}")
        df = df[cfg.use_cols].copy()

    # 日期欄位轉換（若有指定）
    if cfg.date_cols:
        for col in cfg.date_cols:
            if col in df.columns:
                df[col] = stringtodate(df[col])

    return df


# ----------------------------------------------------------------------
# 2. 呼叫 HPM API：把測試資料丟進去
# ----------------------------------------------------------------------
def _build_api_payload(row: pd.Series) -> Dict[str, Any]:
    """
    根據「匯入欄位」組出 HPM API 的 payload。

    ⚠️ 這裡必須依照你的實際 API 參數格式修改。
       下面只是範例（用 row 裡的欄位組 dict），你自己替換即可。
    """
    payload = {
        # TODO：這裡改成你的 HPM API 需要的欄位名稱與對應
        # "cust_id": row["身分證字號"],
        # "apply_amt": float(row["輸入_申請額度"]),
        # "rate": float(row["輸入_利率"]),
    }
    return payload


def call_hpm_api_for_cases(
    df_cases: pd.DataFrame,
    *,
    timeout: float = 10.0,
) -> pd.DataFrame:
    """
    對每一筆 case 呼叫 HPM API，回傳「API 回傳結果的 DataFrame」。

    假設：
      - 每一筆 case 獨立呼叫一次 API
      - 回傳 JSON，可直接組成一列結果

    ※ 若你的 API 支援一次送多筆，可以再另外寫 batch 版。
    """
    results: List[Dict[str, Any]] = []

    for idx, row in df_cases.iterrows():
        payload = _build_api_payload(row)
        resp = requests.post(HPM_API_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        # 讓結果裡也保留 key（方便後面 merge）
        rec: Dict[str, Any] = {}
        # 先把 key 抓進來
        for col in df_cases.columns:
            rec[col] = row[col]

        # 再把 API 的所有欄位展開
        if isinstance(data, dict):
            for k, v in data.items():
                rec[k] = v
        else:
            # 如果 API 回傳不是 dict，你就要依實際結構改這裡
            rec["__raw_api__"] = data

        results.append(rec)

    df_api = pd.DataFrame(results)
    return df_api


# ----------------------------------------------------------------------
# 3. 差異比對：匯入 vs API
# ----------------------------------------------------------------------
def compare_import_vs_api(
    df_import: pd.DataFrame,
    df_api: pd.DataFrame,
    *,
    cfg: VerifyCaseConfig,
    atol: float = 1e-6,
    rtol: float = 0.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    依 cfg.key_cols & cfg.compare_cols 做比對：

    key_cols    : 對齊用 key（匯入端與 API 端都要有）
    compare_cols: {匯入欄名: API欄名}

    回傳：
      (df_merged, df_diff_only)

      - df_merged：所有 case + 匯入欄位 / API 欄位 / 差異欄位
      - df_diff_only：只保留有差異的列
    """
    for col in cfg.key_cols:
        if col not in df_import.columns:
            raise ValueError(f"匯入端缺少 key 欄位：{col}")
        if col not in df_api.columns:
            raise ValueError(f"API 回傳缺少 key 欄位：{col}")

    # merge on keys
    merged = df_import.copy()
    merged = merged.merge(
        df_api,
        on=cfg.key_cols,
        how="left",
        suffixes=("_imp", "_api_raw"),
    )

    # 針對 compare_cols 建出差異欄位
    diff_mask = pd.Series(False, index=merged.index)
    for imp_col, api_col in cfg.compare_cols.items():
        if imp_col not in merged.columns:
            raise ValueError(f"匯入端缺少比對欄位：{imp_col}")
        if api_col not in merged.columns:
            raise ValueError(f"API 回傳缺少比對欄位：{api_col}")

        col_imp = merged[imp_col]
        col_api = merged[api_col]

        # 數值欄位用 atol/rtol 比較，其他用字串比較
        if pd.api.types.is_numeric_dtype(col_imp) and pd.api.types.is_numeric_dtype(col_api):
            diff = (col_imp - col_api).abs() > (atol + rtol * col_api.abs())
        else:
            diff = col_imp.astype("string").fillna("") != col_api.astype("string").fillna("")

        merged[f"DIFF__{imp_col}"] = diff
        diff_mask |= diff

    diff_only = merged[diff_mask].copy()
    return merged, diff_only


# ----------------------------------------------------------------------
# 4. 輸出差異結果
# ----------------------------------------------------------------------
def save_verify_output(
    cfg: VerifyCaseConfig,
    df_merged: pd.DataFrame,
    df_diff_only: pd.DataFrame,
) -> None:
    """
    把比對結果輸出到：
      - HPM_OUTPUT_DIR / f"{cfg.name}_diff.xlsx"
      - HPM_HISTORY_DIR / f"{cfg.name}_merged.parquet"（完整紀錄）
    """
    HPM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HPM_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    out_xlsx = HPM_OUTPUT_DIR / f"{cfg.name}_diff.xlsx"
    hist_pqt = HPM_HISTORY_DIR / f"{cfg.name}_merged.parquet"

    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        df_diff_only.to_excel(writer, sheet_name="diff_only", index=False)
        df_merged.to_excel(writer, sheet_name="all_cases", index=False)

    df_merged.to_parquet(hist_pqt, index=False)

    print(f"[VERIFY] 差異結果已輸出：{out_xlsx}")
    print(f"[VERIFY] 完整紀錄已封存：{hist_pqt}")
