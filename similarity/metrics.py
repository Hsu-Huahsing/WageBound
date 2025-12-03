# similarity/metrics.py

from __future__ import annotations

from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd


def _drop_na_pair(ref: pd.Series, new: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """
    對 ref / new 兩個 series 做「成對去 NA」：
    - 只保留 ref / new 同時不為 NA 的位置。
    - 一律轉成 float 或 string 由上層決定。
    """
    mask = (~ref.isna()) & (~new.isna())
    return ref[mask], new[mask]


# ---------------------------------------------------------------------------
# 1. 連續變數：PSI / KS / 平均數差 / 標準差比
# ---------------------------------------------------------------------------

def calc_psi(ref: pd.Series, new: pd.Series, bins: int = 10) -> float:
    """
    Population Stability Index（分佈穩定度指標）

    直覺：
        - < 0.1   : 非常穩定
        - 0.1~0.25: 有變化，需關注
        - > 0.25  : 分佈已明顯偏移

    做法：
        - 用 ref 的分佈切成等分位 bins
        - 在 ref / new 上計算各 bin 的比例
        - sum( (p_new - p_ref) * ln(p_new / p_ref) )
    """
    ref, new = _drop_na_pair(ref, new)
    if len(ref) == 0 or len(new) == 0:
        return float("nan")

    # 取得分位數切點（避免重複邊界）
    quantiles = np.linspace(0, 1, bins + 1)
    try:
        cuts = np.unique(np.nanpercentile(ref, quantiles * 100))
    except Exception:
        return float("nan")

    if len(cuts) <= 2:
        # 幾乎沒有分佈可言
        return 0.0

    # 將 ref / new 依據 ref 的切點分箱
    ref_bins = pd.cut(ref, bins=cuts, include_lowest=True)
    new_bins = pd.cut(new, bins=cuts, include_lowest=True)

    ref_counts = ref_bins.value_counts().sort_index()
    new_counts = new_bins.value_counts().sort_index()

    ref_pct = ref_counts / ref_counts.sum()
    new_pct = new_counts / new_counts.sum()

    # 避免 log(0)：把 0 拉到一個很小的 epsilon
    epsilon = 1e-8
    ref_pct = ref_pct.clip(lower=epsilon)
    new_pct = new_pct.clip(lower=epsilon)

    psi = ((new_pct - ref_pct) * np.log(new_pct / ref_pct)).sum()
    return float(psi)


def calc_ks(ref: pd.Series, new: pd.Series) -> float:
    """
    KS 統計量：兩個連續分佈之間最大 CDF 差異。
    """
    ref, new = _drop_na_pair(ref, new)
    if len(ref) == 0 or len(new) == 0:
        return float("nan")

    ref_sorted = np.sort(ref.to_numpy())
    new_sorted = np.sort(new.to_numpy())

    all_values = np.unique(np.concatenate([ref_sorted, new_sorted]))
    # CDF
    ref_cdf = np.searchsorted(ref_sorted, all_values, side="right") / len(ref_sorted)
    new_cdf = np.searchsorted(new_sorted, all_values, side="right") / len(new_sorted)

    ks = np.max(np.abs(ref_cdf - new_cdf))
    return float(ks)


def calc_numeric_stats(ref: pd.Series, new: pd.Series) -> Dict[str, float]:
    """
    給連續變數的基礎統計比較：
        - mean_diff     : new_mean - ref_mean
        - mean_ratio    : new_mean / ref_mean
        - std_ratio     : new_std  / ref_std
    """
    ref, new = _drop_na_pair(ref, new)
    if len(ref) == 0 or len(new) == 0:
        return {
            "mean_ref": float("nan"),
            "mean_new": float("nan"),
            "mean_diff": float("nan"),
            "mean_ratio": float("nan"),
            "std_ref": float("nan"),
            "std_new": float("nan"),
            "std_ratio": float("nan"),
        }

    mean_ref = float(ref.mean())
    mean_new = float(new.mean())
    std_ref = float(ref.std(ddof=1)) if len(ref) > 1 else float("nan")
    std_new = float(new.std(ddof=1)) if len(new) > 1 else float("nan")

    mean_diff = mean_new - mean_ref
    mean_ratio = mean_new / mean_ref if mean_ref != 0 else float("inf")
    std_ratio = std_new / std_ref if std_ref != 0 else float("inf")

    return {
        "mean_ref": mean_ref,
        "mean_new": mean_new,
        "mean_diff": mean_diff,
        "mean_ratio": mean_ratio,
        "std_ref": std_ref,
        "std_new": std_new,
        "std_ratio": std_ratio,
    }


# ---------------------------------------------------------------------------
# 2. 類別變數：分佈距離（Jensen–Shannon）＋類別差異
# ---------------------------------------------------------------------------

def calc_categorical_distance(ref: pd.Series, new: pd.Series) -> Dict[str, Any]:
    """
    類別變數相似度：

    回傳：
        - js_div    : Jensen–Shannon divergence（0 越近似）
        - top_diff  : 各類別比例差 |p_new - p_ref|，從大到小排序後列出前幾名
    """
    ref, new = _drop_na_pair(ref.astype("string"), new.astype("string"))
    if len(ref) == 0 or len(new) == 0:
        return {"js_div": float("nan"), "top_diff": []}

    ref_counts = ref.value_counts(normalize=True)
    new_counts = new.value_counts(normalize=True)

    all_cats = sorted(set(ref_counts.index).union(set(new_counts.index)))
    ref_vec = np.array([ref_counts.get(c, 0.0) for c in all_cats], dtype=float)
    new_vec = np.array([new_counts.get(c, 0.0) for c in all_cats], dtype=float)

    # 加 epsilon 避免 log(0)
    epsilon = 1e-12
    ref_vec = ref_vec + epsilon
    new_vec = new_vec + epsilon

    m = 0.5 * (ref_vec + new_vec)

    kl_ref = np.sum(ref_vec * np.log(ref_vec / m))
    kl_new = np.sum(new_vec * np.log(new_vec / m))
    js_div = 0.5 * (kl_ref + kl_new)

    # 類別差異排序
    diff = np.abs(new_vec - ref_vec)
    order = np.argsort(-diff)
    top_diff = [
        {"category": all_cats[i], "p_ref": float(ref_vec[i]), "p_new": float(new_vec[i]), "abs_diff": float(diff[i])}
        for i in order
    ]

    return {"js_div": float(js_div), "top_diff": top_diff}
