from typing import List, Dict, Any, Optional
import pandas as pd
from StevenTricks.convert_utils import stringtodate
from .engine import compute_similarity

def run_similarity_search(
    df: pd.DataFrame,
    target_idx: Any,
    feature_cols: List[str],
    *,
    date_cols: Optional[List[str]] = None,
    date_mode: int = 4,
    top_k: int = 20,
    weight_conf: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    """
    - df: 全部案件
    - target_idx: 目標案件在 df 的 index（或你要改成 primary key 也可以）
    - feature_cols: 拿來算相似度的欄位（其餘欄位不參與計算，但會被保留回傳讓你看）
    - date_cols: 如果有日期欄位（ex '核准日'），這裡會用 stringtodate() 統一轉成 datetime
    """
    work = df.copy()

    # 1) 處理日期欄位
    if date_cols:
        work = stringtodate(work, date_cols, mode=date_mode)

    # 2) 只挑出要用來算相似度的欄位，避免巨大 df 拖慢
    feature_cols = [c for c in feature_cols if c in work.columns]

    # 3) 抓目標 row
    try:
        target_row = work.loc[target_idx]
    except KeyError:
        raise KeyError(f"target_idx {target_idx!r} 不在 df.index 裡")

    # 4) 把 target 自己先排除，再送進引擎
    others = work.drop(index=[target_idx])

    result = compute_similarity(
        df=others,
        target_row=target_row,
        feature_cols=feature_cols,
        weight_conf=weight_conf,
        top_k=top_k,
    )

    return result
