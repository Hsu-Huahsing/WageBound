# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:09:24 2025

@author: Z00051711
"""

"""
情境 1：大表 + 原始日期欄是亂格式（比如 ROC / 0820412 / 20250909）
from StevenTricks.driver_tree import build_mom_driver_tree

tree = build_mom_driver_tree(
    df=df_big,
    month_col="Month",            # 想要的「月份欄位名稱」
    value_col="Funding_Amt",
    dims=["產品別", "分行別"],
    segment_filter={"區域": "北區"},
    target_month="2025-09-01",
    max_depth=3,
    min_r2=0.05,
    min_share=0.1,
    date_col="raw_date",          # 原始日期欄（裡面可能是 0820412 / 20250909 等）
    date_mode=4,                  # 對應你在 stringtodate 裡設定的模式
    use_cols=[
        "raw_date", "產品別", "分行別", "區域", "Funding_Amt"
    ],
)
流程：
1.	先把 df_big 縮成只剩上面這幾個欄位。
2.	raw_date 先丟給 stringtodate(..., mode=4)，再補一層 to_datetime。
3.	如果 df 原本沒有 "Month"，就用 raw_date.dt.to_period("M").dt.to_timestamp() 生出每月第一天。
4.	用這個 Month 去做 MoM 聚合 + driver tree。
________________________________________
情境 2：你自己已經先做好 Month 欄（YYYY-MM-01 字串）
df["Month"] = df["month_str"]  # 例如 '2025-09-01'

tree = build_mom_driver_tree(
    df=df,
    month_col="Month",
    value_col="Funding_Amt",
    dims=["A", "B", "C"],
    segment_filter={"A": "A1"},
    target_month="2025-09-01",
    date_col=None,      # 不用再處理原始日期
    use_cols=["Month", "A", "B", "C", "Funding_Amt"],
)
這個情境下：
•	不會呼叫 stringtodate。
•	只會把 Month 嘗試轉成 datetime64（因為我們在 (B) 那段有做一層 to_datetime，前提是 date_col 不存在；但這版我們只在有 date_col 時才動，所以這個情境 Month 是你原本的欄位、你自己保證 OK）。
如果你希望這個情境也強制 Month 轉成 datetime，可以在呼叫前自己做：
df["Month"] = pd.to_datetime(df["Month"])。
"""


import pandas as pd
from StevenTricks.driver_tree import (
    build_mom_driver_tree,
    format_driver_story,
)

data = [
    ('2025-09', 'A1', 'B1', 'C1', 'D1', 'E1', 1000),
    ('2025-09', 'A1', 'B1', 'C2', 'D1', 'E1', 100),
    ('2025-09', 'A1', 'B2', 'C1', 'D1', 'E1', 1000000000),
    ('2025-09', 'A1', 'B2', 'C2', 'D1', 'E1', 1000),
    ('2025-10', 'A1', 'B1', 'C1', 'D1', 'E1',  50),
    ('2025-10', 'A1', 'B1', 'C2', 'D1', 'E1',  950000),
    ('2025-10', 'A1', 'B2', 'C1', 'D1', 'E1', 105000),
    ('2025-10', 'A1', 'B2', 'C2', 'D1', 'E1', 10500),
]

df = pd.DataFrame(data, columns=['Month','A','B','C','D','E','Funding_Amt'])
df['Month'] = pd.to_datetime(df['Month'])

tree = build_mom_driver_tree(
    df=df,
    month_col="Month",
    value_col="Funding_Amt",
    dims=["A", "B", "C", "D", "E"],
    segment_filter={"B": "B2"},
    target_month="2025-10-01",
    max_depth=3,
    min_r2=0.05,
    min_share=0.1,
)

print(
    format_driver_story(
        tree,
        segment_name="B2 客群",
        target_month="2025-10",
        metric_name="Funding_Amt",
        unit="元",
    )
)

