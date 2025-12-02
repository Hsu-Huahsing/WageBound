# WageBound/config/verify_config.py

from pathlib import Path
from .config import ROOT_DIR  # 如果你有定義專案根目錄，沒有就自己寫

# HPM 測試檔路徑
HPM_TEST_XLSX = Path(r"D:\數位專案\HPM2.0\...你原本的測試檔.xlsx")

# HPM API URL
HPM_API_URL = "http://localhost:8080/HPMVerify"

# HPM 歷史輸出、封存路徑
HPM_OUTPUT_DIR  = Path(r"D:\...\HPM_output")
HPM_HISTORY_DIR = Path(r"D:\...\HPM_history")

# 要檢核的主要欄位 mapping（匯入 vs API 回傳）
HPM_COMPARE_COLS = {
    "輸入_申請額度": "apply_amt",
    "輸入_利率": "rate",
    "輸出_核准額度": "APPROVED_AMT",
    "輸出_DB R": "DBR",
    # 這些名字你照你 Excel 檔 & API 結構自己填
}
