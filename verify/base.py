# WageBound/verify/base.py
import pandas as pd
from pathlib import Path

def load_hpm_test_cases(path: Path, *, sheet: str | int = 0) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet)
    # 這裡可以做共用清理：去空白、欄位 rename...
    return df
import requests

def call_hpm_api(row: pd.Series, *, url: str, timeout: int = 30) -> dict:
    # 依你現在 hpm_verify_api.py 的傳參數格式整理
    payload = {
        "CustId": row["客戶ID"],
        "LoanAmt": row["申請額度"],
        # ...
    }
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
def compare_case(
    row: pd.Series,
    api_result: dict,
    compare_cols: dict[str, str],
) -> dict:
    """
    compare_cols: { 'Excel欄位名': 'API回傳欄位名' }
    回傳一個 dict，列出每個欄位是否一致、差異值。
    """
    out = {"case_id": row.get("CaseID")}
    for xcol, api_key in compare_cols.items():
        expected = row.get(xcol)
        actual = api_result.get(api_key)
        out[f"{xcol}_expected"] = expected
        out[f"{xcol}_actual"] = actual
        out[f"{xcol}_is_equal"] = (expected == actual)
    return out
