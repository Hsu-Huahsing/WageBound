# similarity/engine.py

from __future__ import annotations

from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from .metrics import (
    calc_psi,
    calc_ks,
    calc_numeric_stats,
    calc_categorical_distance,
)


def _is_numeric(series: pd.Series) -> bool:
    """
    判斷欄位是否視為「連續數值」：
        - dtype 為 number
        - 或是混雜但經過 to_numeric 有大部分能轉成功
    """
    if pd.api.types.is_numeric_dtype(series):
        return True

    # 嘗試強制轉 numeric 看成功比例
    converted = pd.to_numeric(series, errors="coerce")
    ratio = converted.notna().mean()
    return ratio >= 0.7


def _prepare_feature_list(
    df_ref: pd.DataFrame,
    df_new: pd.DataFrame,
    feature_cols: Optional[List[str]],
) -> List[str]:
    """
    決定要分析的欄位：
        - 若有指定 feature_cols：取兩邊都有的交集
        - 否則：自動抓兩邊共同的欄位（排除明顯 id 欄）
    """
    common = sorted(set(df_ref.columns).intersection(set(df_new.columns)))

    if feature_cols:
        cols = [c for c in feature_cols if c in common]
    else:
        # 自動模式：先拿共同欄位，再排除些常見 ID 欄
        blacklist = {"id", "ID", "cust_id", "CUST_ID", "customer_id"}
        cols = [c for c in common if c not in blacklist]

    return cols


def run_similarity(
    df_ref: pd.DataFrame,
    df_new: pd.DataFrame,
    *,
    feature_cols: Optional[List[str]] = None,
    max_top_diff: int = 5,
    psi_bins: int = 10,
) -> pd.DataFrame:
    """
    高階封裝：比較兩個 DataFrame 在各欄位上的分佈相似度。

    典型用法：
        result = run_similarity(
            df_ref=dev_df,         # 例如：歷史母體
            df_new=oos_df,         # 例如：新申請或新制
            feature_cols=["age", "income", "ltv"],  # 可選，不給就自動抓共同欄位
        )

    回傳欄位（數值型）：
        - feature        : 欄位名稱
        - type           : "numeric"
        - psi            : PSI
        - ks             : KS
        - mean_ref       : 參考樣本平均
        - mean_new       : 新樣本平均
        - mean_diff      : 差值
        - mean_ratio     : 比例
        - std_ref        : 標準差（參考）
        - std_new        : 標準差（新樣本）
        - std_ratio      : 比例
        - n_ref / n_new  : 各樣本有效樣本數

    回傳欄位（類別型）：
        - feature        : 欄位名稱
        - type           : "categorical"
        - js_div         : Jensen–Shannon divergence
        - top_diff       : 前幾大類別比例差異（list[dict]）
        - n_ref / n_new  : 各樣本有效樣本數
    """
    # 對齊欄位
    cols = _prepare_feature_list(df_ref, df_new, feature_cols)
    if not cols:
        raise ValueError("run_similarity(): 找不到可比較的欄位，請檢查 feature_cols 或 df_ref/df_new 的欄位交集。")

    results: List[Dict[str, Any]] = []

    for col in cols:
        s_ref = df_ref[col]
        s_new = df_new[col]

        # 成對去 NA
        mask_pair = (~s_ref.isna()) & (~s_new.isna())
        s_ref2 = s_ref[mask_pair]
        s_new2 = s_new[mask_pair]

        n_ref = int(len(s_ref2))
        n_new = int(len(s_new2))

        if n_ref == 0 or n_new == 0:
            results.append(
                {
                    "feature": col,
                    "type": "unknown",
                    "note": "兩邊皆無有效資料，略過",
                    "n_ref": n_ref,
                    "n_new": n_new,
                }
            )
            continue

        if _is_numeric(s_ref2):
            # 數值型
            numeric_stats = calc_numeric_stats(s_ref2, s_new2)
            psi_val = calc_psi(pd.to_numeric(s_ref2, errors="coerce"),
                               pd.to_numeric(s_new2, errors="coerce"),
                               bins=psi_bins)
            ks_val = calc_ks(pd.to_numeric(s_ref2, errors="coerce"),
                             pd.to_numeric(s_new2, errors="coerce"))

            row: Dict[str, Any] = {
                "feature": col,
                "type": "numeric",
                "psi": psi_val,
                "ks": ks_val,
                "n_ref": n_ref,
                "n_new": n_new,
            }
            row.update(numeric_stats)
            results.append(row)
        else:
            # 類別型
            cat_stats = calc_categorical_distance(s_ref2, s_new2)
            top_diff = cat_stats["top_diff"][:max_top_diff]
            results.append(
                {
                    "feature": col,
                    "type": "categorical",
                    "js_div": cat_stats["js_div"],
                    "top_diff": top_diff,
                    "n_ref": n_ref,
                    "n_new": n_new,
                }
            )

    summary = pd.DataFrame(results)

    # 小排序：數值欄位以 PSI 由大到小，類別以 js_div 由大到小
    def _sort_key(row):
        if row["type"] == "numeric":
            return row.get("psi", 0.0)
        if row["type"] == "categorical":
            return row.get("js_div", 0.0)
        return 0.0

    summary = summary.sort_values(
        by=summary.apply(_sort_key, axis=1).name,
        ascending=False,
    )

    # 上面 sort_values 的 key trick 比較醜，你不喜歡可以改成：
    # summary["sort_score"] = summary.apply(_sort_key, axis=1)
    # summary = summary.sort_values("sort_score", ascending=False).drop(columns=["sort_score"])

    return summary
