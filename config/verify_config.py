# config/verify_config.py
# -*- coding: utf-8 -*-
"""
驗證規則設定檔（只放「規則資料」，不放程式邏輯）

這裡只是一個範例：
- 針對放款資料表：檢查必要欄位 / 型別 / 合理範圍
- 針對 DBR / ATD / 成數 等欄位預留規則

實務上你可以依照實際欄位改寫：
    Loan_Amt, Income_Amt, DBR, ATD, Grace_Months, Tenor_Months, Region_Level...
"""

from __future__ import annotations
from typing import Dict, Any, List, Literal

# 支援多種「場景」的規則，例如：'new_loan', 'topup', 'portfolio_snapshot'
# 先處理一個通用的 'wagebound_main'
SCENES: Dict[str, Dict[str, Any]] = {
    "wagebound_main": {
        "required_columns": [
            "Cust_ID",
            "Contract_No",
            "Drawdown_Date",     # 放款日期
            "Maturity_Date",     # 到期日
            "Region_Level",      # 區域等級
            "Customer_Level",    # 客層等級
            "Loan_Amt",          # 放款金額
            "Income_Amt",        # 年收入
            "DBR",
            "ATD",
            "Grace_Months",      # 寬限期（月）
            "Tenor_Months",      # 總貸款期限（月）
            "LTV_Flag",          # LTV flag / 专案 flag
        ],
        # 欄位預期 dtype，建議只管「關鍵欄位」
        "expected_dtypes": {
            "Cust_ID": "string",
            "Contract_No": "string",
            "Drawdown_Date": "datetime64[ns]",
            "Maturity_Date": "datetime64[ns]",
            "Region_Level": "string",
            "Customer_Level": "string",
            "Loan_Amt": "float64",
            "Income_Amt": "float64",
            "DBR": "float64",
            "ATD": "float64",
            "Grace_Months": "Int64",
            "Tenor_Months": "Int64",
            "LTV_Flag": "string",
        },
        # 數值欄位合理範圍（下限、上限）→ 超出就列為異常
        "numeric_ranges": {
            "Loan_Amt": (0, None),          # >0
            "Income_Amt": (0, None),
            "DBR": (0, 3),                  # 0~300% 之類
            "ATD": (0, 5),
            "Grace_Months": (0, 120),
            "Tenor_Months": (1, 480),
        },
        # 允許為空值的欄位（其他必要欄位若為空就會被抓出來）
        "nullable_columns": [
            "Maturity_Date",
            "Grace_Months",
        ],
    }
}
