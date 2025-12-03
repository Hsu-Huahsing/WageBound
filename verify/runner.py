import pandas as pd
from verify.runner import verify_dataframe

# 1) 原始 data 讀進來（CSV / DB / PKL 都可）
df = pd.read_csv("some_big_raw_table.csv")

# 2) 僅選你要分析的欄位也沒問題（verify 會只用到規則裡有設定的欄位）
use_cols = [
    "Cust_ID", "Contract_No", "Drawdown_Date", "Maturity_Date",
    "Region_Level", "Customer_Level",
    "Loan_Amt", "Income_Amt", "DBR", "ATD",
    "Grace_Months", "Tenor_Months", "LTV_Flag",
]
df_use = df[use_cols].copy()

# 3) 直接丟進去驗證
issues = verify_dataframe(df_use, scene="wagebound_main")

if issues.empty:
    print("驗證通過，沒有異常。")
else:
    print("驗證發現異常筆數：", len(issues))
    print(issues.head())
