# -*- coding: utf-8 -*-
"""
DriverTree / ScenarioCompare 測試腳本

用法概念：
1. demo_driver_tree_with_toy_data()
   - 完全用程式內建的小型假資料，確認安裝與 API 沒問題。

2. demo_driver_tree_with_real_excel()
   - 讀取你自己的 Excel（例如 202510新貸放客戶_part.xlsx），
     跑「當月 vs 上月」的 Driver Tree。

3. demo_scenario_compare_with_real_excel()
   - 針對同一份 Excel，做多情境（Scenario）的樞紐比較。

注意：
- 匯入方式固定用：
    from StevenTricks.analysis import (driver_tree, scenario_compare)
- 你只需要改：EXCEL_PATH、欄位對應 rename_map、dims、scenarios。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Callable

import pandas as pd
from StevenTricks.analysis import (driver_tree, scenario_compare)


# ----------------------------------------------------------------------
# 共用：讀取真實 Excel 的小工具
# ----------------------------------------------------------------------
def load_funding_excel(
    excel_path: str | Path,
    sheet_name: int | str = 0,
    *,
    rename_map: Dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    讀取「新貸放客戶」類型的 Excel，整理成 DriverTree / ScenarioCompare 共用格式。

    讀完後我們希望至少具備這些欄位（名字是下游程式會用到的）：
        - Funding_Date_yymm : str，例如 "202509", "202510"
        - Funding_Amt       : float
        - 其他維度欄位：例如 Product_Flag_new, Property_Location_Flag, Cust_Flag, ...

    參數說明
    ----------
    excel_path : 檔案路徑
    sheet_name : 要讀的工作表，預設第 1 張
    rename_map : 可選，{原始欄名: 目標欄名} 的 dict
                 用來把中文欄名改成程式裡習慣的英文欄名。
    """
    excel_path = Path(excel_path)
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # 1) 欄位改名（如果你的 Excel 已經是英文欄位，可把 rename_map 設為 None）
    if rename_map:
        df = df.rename(columns=rename_map)

    # 2) 處理日期欄位：確保有 Funding_Date_yymm（202509 這種六碼字串）
    if "Funding_Date_yymm" not in df.columns:
        # 假設原始有 "Funding_Date"（完整日期），用它生 yyyymm
        if "Funding_Date" not in df.columns:
            raise KeyError(
                "資料裡找不到 'Funding_Date_yymm' 或 'Funding_Date'，"
                "請在 rename_map 裡把你的日期欄位對應到其中一個名稱。"
            )
        df["Funding_Date"] = pd.to_datetime(df["Funding_Date"])
        df["Funding_Date_yymm"] = df["Funding_Date"].dt.strftime("%Y%m")

    # 統一成六碼字串
    df["Funding_Date_yymm"] = df["Funding_Date_yymm"].astype(str).str.slice(0, 6)

    # 3) 金額欄位轉成 float（避免字串 / NaN 搗亂）
    if "Funding_Amt" not in df.columns:
        raise KeyError("資料裡找不到 'Funding_Amt' 欄位，請在 rename_map 把實際金額欄位對應到 'Funding_Amt'。")

    df["Funding_Amt"] = pd.to_numeric(df["Funding_Amt"], errors="coerce").fillna(0.0)

    return df


# ----------------------------------------------------------------------
# 情境 1：toy data 版本（完全在記憶體裡造一個小表）
# ----------------------------------------------------------------------
def demo_driver_tree_with_toy_data():
    """
    用非常小的假資料跑一次 Driver Tree，
    只為了確認：模組可以 import、流程 OK、輸出長相如何。
    """
    data = [
        ('2025-09', 'A1', 'B1', 'C1', 'D1', 'E1', 1000),
        ('2025-09', 'A1', 'B1', 'C2', 'D1', 'E1', 100),
        ('2025-09', 'A1', 'B2', 'C1', 'D1', 'E1', 1000000000),
        ('2025-09', 'A1', 'B2', 'C2', 'D1', 'E1', 1000),
        ('2025-10', 'A1', 'B1', 'C1', 'D1', 'E1', 50),
        ('2025-10', 'A1', 'B1', 'C2', 'D1', 'E1', 950000),
        ('2025-10', 'A1', 'B2', 'C1', 'D1', 'E1', 105000),
        ('2025-10', 'A1', 'B2', 'C2', 'D1', 'E1', 10500),
    ]
    df = pd.DataFrame(data, columns=['Month', 'A', 'B', 'C', 'D', 'E', 'Funding_Amt'])
    # 這裡的 Month 直接當作「yyyymm」，所以轉成 "202509" / "202510" 形式
    df["Funding_Date_yymm"] = pd.to_datetime(df["Month"]).dt.strftime("%Y%m")

    # 實際跑 Driver Tree：比較 202509 vs 202510
    result = driver_tree.run_driver_tree_change(
        df=df,
        base_period="202509",
        comp_period="202510",
        dims=["A", "B", "C", "D", "E"],   # 想要讓 Driver Tree 自動切的維度
        target_col="Funding_Amt",
        time_col="Funding_Date_yymm",
        max_depth=3,
        min_node_share=0.05,
        top_k=5,
    )

    nodes_df = result["nodes_df"]
    print("=== Toy Data Driver Tree 節點摘要 ===")
    print(nodes_df[["node_id", "depth", "path", "delta_amt", "delta_share", "summary_zh"]])

    return nodes_df


# ----------------------------------------------------------------------
# 情境 2：用真實 Excel 跑 Driver Tree
# ----------------------------------------------------------------------
def demo_driver_tree_with_real_excel():
    """
    讀取真實新貸資料（.xlsx），跑「當月 vs 上月」的 Driver Tree。

    使用方式：
        1. 把 EXCEL_PATH 換成你的「202510新貸放客戶_part.xlsx」實際路徑。
        2. 依照你 Excel 的欄位名稱，調整 rename_map。
        3. 視需要調整 base_period / comp_period 和 dims。
    """
    # 1) 設定 Excel 路徑
    EXCEL_PATH = "/Users/stevenhsu/Library/Mobile Documents/.../202510新貸放客戶_part.xlsx"

    # 2) 把中文欄位名對應成程式使用的欄位名
    #    若你的 Excel 本來就用這些英文欄名，可以把 rename_map 改成 {} 或 None
    rename_map = {
        # 日期與金額
        "放款年月": "Funding_Date_yymm",   # 若原檔是 yyyymm 整數 / 字串
        "放款金額": "Funding_Amt",

        # 下面這些只是示意，請依照你實際欄名對應
        "產品別": "Product_Flag_new",
        "地區別": "Property_Location_Flag",
        "年期別": "Tenor_Flag",
        "寬限期長度別": "Grace_Length_Flag",
        "OLTV 切分": "OLTV_Flag",
        "客戶別": "Cust_Flag",
        "帳戶型態": "Acct_Type_Code",
        "利率型態": "Int_Category_Code",
        "專案批次": "Batch_Flag",
        "特殊專案註記": "special_flag",
        "投資人註記": "Investor_Flag",
        "公開發行註記2024": "Public_Flag2024",
        "轉換公司債投資人註記": "cb_Investor_flag",
    }

    # 3) 讀 Excel → 整理成統一格式
    df = load_funding_excel(EXCEL_PATH, sheet_name=0, rename_map=rename_map)

    # 4) 跑 Driver Tree：比較 202509 vs 202510
    result = driver_tree.run_driver_tree_change(
        df=df,
        base_period="202509",
        comp_period="202510",
        # 你想讓 Driver Tree 自動切分的維度（可以隨時增減）
        dims=[
            "Product_Flag_new",
            "Property_Location_Flag",
            "Tenor_Flag",
            "Grace_Length_Flag",
            "OLTV_Flag",
            "Cust_Flag",
            "Acct_Type_Code",
            "Int_Category_Code",
            "Batch_Flag",
            "special_flag",
            "Investor_Flag",
            "Public_Flag2024",
            "cb_Investor_flag",
        ],
        target_col="Funding_Amt",
        time_col="Funding_Date_yymm",
        max_depth=3,
        min_node_share=0.03,   # 分支太小就不繼續往下拆
        top_k=8,               # 只看貢獻最大的前幾個節點
    )

    nodes_df = result["nodes_df"]

    print("=== 真實 Excel Driver Tree：主因節點（依 |delta_amt| 排序）===")
    print(
        nodes_df.sort_values("abs_delta_amt", ascending=False)[
            ["node_id", "depth", "path", "delta_amt", "delta_share", "summary_zh"]
        ].head(20)
    )

    # 方便你在 IPython 裡繼續玩
    return nodes_df


# ----------------------------------------------------------------------
# 情境 3：用真實 Excel 跑 Scenario Compare
# ----------------------------------------------------------------------
def demo_scenario_compare_with_real_excel():
    """
    讀同一份 Excel，針對不同情境做樞紐比較。

    典型情境：
        - 全體客群
        - 有寬限期者
        - DBR 評分的寬限案
        - ATD 評分的寬限案
        - 高 OLTV 子樣本

    你可以按自己的習慣調整 scenarios 裡的條件。
    """
    EXCEL_PATH = "/Users/stevenhsu/Library/Mobile Documents/.../202510新貸放客戶_part.xlsx"

    # 跟上面 Driver Tree 一樣的 rename_map，避免每段都各自亂改名
    rename_map = {
        "放款年月": "Funding_Date_yymm",
        "放款金額": "Funding_Amt",
        "產品別": "Product_Flag_new",
        "地區別": "Property_Location_Flag",
        "年期別": "Tenor_Flag",
        "寬限期長度別": "Grace_Length_Flag",
        "OLTV 切分": "OLTV_Flag",
        "客戶別": "Cust_Flag",
        "評分方式": "Eval_Type",          # 例如 "DBR" / "ATD"
        "寬限期註記": "Grace_Flag",       # 0/1 或 Y/N
    }

    df = load_funding_excel(EXCEL_PATH, sheet_name=0, rename_map=rename_map)

    # 如果你只想看某一個月份，可以先切出該月
    df_202510 = df[df["Funding_Date_yymm"] == "202510"].copy()

    # 定義各種情境（Scenario）：對 DataFrame 回傳 boolean mask 的函數
    # 欄位名稱請對應上面 rename 後的名字
    scenarios: Dict[str, Callable[[pd.DataFrame], pd.Series]] = {
        "all": lambda d: d["Funding_Amt"] > 0,
        "grace_all": lambda d: d["Grace_Flag"] == 1,
        "grace_DBR": lambda d: (d["Grace_Flag"] == 1) & (d["Eval_Type"] == "DBR"),
        "grace_ATD": lambda d: (d["Grace_Flag"] == 1) & (d["Eval_Type"] == "ATD"),
        "high_OLTV": lambda d: d["OLTV_Flag"].isin(["80%以上", "90%以上"]),
    }

    # 想在樞紐表上當作 row / column 的維度
    dims = ["Property_Location_Flag", "Cust_Flag"]

    res = scenario_compare.summarize_scenarios(
        df=df_202510,
        dims=dims,
        value_col="Funding_Amt",
        scenarios=scenarios,
        base_scenario="all",  # 用來算「與全體差異」
    )

    print("=== Scenario Compare：wide_with_diff（前幾列）===")
    print(res.wide_with_diff.head(20))

    # 若你想直接輸出成 Excel：
    # out_xlsx = Path(EXCEL_PATH).with_name("ScenarioCompare_202510.xlsx")
    # scenario_compare.export_result_to_excel(res, out_xlsx)

    return res


# ----------------------------------------------------------------------
# 直接當 script 跑時的入口
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 1) 先確認 toy data 可以正常跑
    demo_driver_tree_with_toy_data()

    # 2) 再用真實 Excel 跑 Driver Tree / Scenario Compare
    #    （EXCEL_PATH / rename_map 調好之後再解註解）
    # demo_driver_tree_with_real_excel()
    # demo_scenario_compare_with_real_excel()
