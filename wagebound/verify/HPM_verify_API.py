# -*- coding: utf-8 -*-
"""
DGIS AccurateEstimation API 測試 & Log 產出
- 讀取來源 Excel / pkl
- 組 API payload
- 並行呼叫 AccurateEstimation
- 拆出 PCSMINPUT / PCSMOUTPUT / CompareCase(LVR、CTBC_Inside)
- 匯出 Excel log

Created on Mon Sep 23 14:13:18 2024
@author: Z00051711
"""

import json
from os.path import join, exists
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests
from tqdm import tqdm

from StevenTricks.fileop import pickleload, picklesave
from wagebound.config.config import comparecase_select, clean_colname


# =============================================================================
# 0. 基本參數
# =============================================================================

# datapath = r"D:\數位專案\透天房地分離\2025_6RC\驗證用"
datapath = r"E:\數位專案\HPM2.0\2025-11RC\改辦法\驗證用資料"
source_file = "DGIS_InOutJson_0913.xlsx"

Type = "uat"        # or "sit"
MAX_CASES = None    # 若只想測試前 N 筆，改成整數，例如 1000

url_dict = {
    "sit": r"http://dgisapiuat.ctbcbank.com:8080/dgis/dgisapi/AccurateEstimation",
    "uat": r"http://dgisapiuat.ctbcbank.com/dgis/dgisapi/AccurateEstimation",
}

source_pkl = join(datapath, "source.pkl")
apiresult_pkl = join(datapath, f"{Type}Result.pkl")


# =============================================================================
# 1. 小工具
# =============================================================================

def call_api(payload: dict):
    """
    打 AccurateEstimation API，回傳：
    (caseno, collateralno, output_json, input_json, conn_flag)
    """
    try:
        resp = requests.post(url_dict[Type], json=payload, timeout=10)
        resp.raise_for_status()
        resjson = resp.json()
    except Exception as e:
        cdata = payload.get("CollateralData", {})
        return (
            cdata.get("CaseNo"),
            cdata.get("CollateralNo"),
            {"Success": False, "Error": str(e)},
            payload,
            False,
        )

    success = resjson.get("Success", False)
    if not success:
        cdata = payload.get("CollateralData", {})
        caseno = cdata.get("CaseNo")
        collateralno = cdata.get("CollateralNo")
        conn = False
    else:
        result = resjson.get("Result", {})
        caseno = result.get("CaseNo")
        collateralno = result.get("CollateralNo")
        conn = True

    return caseno, collateralno, resjson, payload, conn


def dict_to_df(features: list) -> pd.DataFrame:
    """將 comparecase 裡的 features 轉成 DataFrame（只取 properties）。"""
    if not features:
        return pd.DataFrame()
    return pd.DataFrame([f.get("properties", {}) for f in features])


# =============================================================================
# 2. 讀取來源資料（Excel / pkl）
# =============================================================================

if exists(source_pkl):
    data = pickleload(source_pkl)
else:
    data = pd.read_excel(join(datapath, source_file))
    picklesave(data, source_pkl)

# =============================================================================
# 3. 組 dgisinput（CollateralData 展開）與 apiinput（原始 json payload）
# =============================================================================

dgis_rows = []
apiinput = []

for applno, inputjson in data[["ApplNo", "InputJson"]].itertuples(index=False):
    payload = json.loads(inputjson)

    collateral = payload.get("CollateralData", {})
    collateral["applno_RawData"] = applno

    # 確保一定有 CommunityFlag 欄位，避免 API schema 檢查出錯
    collateral.setdefault("CommunityFlag", "")

    dgis_rows.append(collateral)
    apiinput.append(payload)

dgisinput = pd.DataFrame(dgis_rows)

# =============================================================================
# 4. 準備 / 取得 API 結果（可重複使用 cache）
# =============================================================================

if exists(apiresult_pkl):
    apiresult = pickleload(apiresult_pkl)
else:
    max_workers = 10
    targets = apiinput if MAX_CASES is None else apiinput[:MAX_CASES]

    print("AccurateEstimation API 呼叫開始:", datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        apiresult = list(tqdm(pool.map(call_api, targets), total=len(targets)))
    print("AccurateEstimation API 呼叫結束:", datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

    picklesave(apiresult, apiresult_pkl)

# 有需要查單筆時，可以用這個 DataFrame filter
apiresult_df = pd.DataFrame(
    apiresult,
    columns=["caseno", "collateralno", "output_json", "input_json", "conn"],
)

# =============================================================================
# 5. 解析 API 結果：PCSMINPUT / PCSMOUTPUT / CompareCase（LVR & CTBC_Inside）
# =============================================================================

lvr_out = pd.DataFrame()
ctbc_inside_out = pd.DataFrame()
pcsm_input = pd.DataFrame()
pcsm_output = pd.DataFrame()

for caseno, collateralno, apioutput, input_data, conn in apiresult:
    if not conn:
        print("連線失敗：", caseno)
        continue

    pcsm = apioutput.get("PerformanceStatistic", {})
    if "PCSMINPUT" not in pcsm or "PCSMOUTPUT" not in pcsm:
        print("PCSM 結構錯誤：", caseno)
        continue

    # ---- PCSM input / output ----
    pcsm_in_tmp = pd.DataFrame([pcsm["PCSMINPUT"]])
    pcsm_out_tmp = pd.DataFrame([pcsm["PCSMOUTPUT"]])

    pcsm_in_tmp["applno"] = caseno
    pcsm_in_tmp["CollateralNo"] = collateralno
    pcsm_out_tmp["applno"] = caseno
    pcsm_out_tmp["CollateralNo"] = collateralno

    pcsm_input = pd.concat([pcsm_input, pcsm_in_tmp], ignore_index=True)
    pcsm_output = pd.concat([pcsm_output, pcsm_out_tmp], ignore_index=True)

    # ---- CompareCase：LVR & CTBC_Inside ----
    comparecase = comparecase_select(apioutput["Result"]["CompareCase"])
    lvr_df = dict_to_df(comparecase.get("LVR", []))
    ctbc_inside_df = dict_to_df(comparecase.get("CTBC_Inside", []))

    if not lvr_df.empty:
        lvr_df["applno"] = caseno
        lvr_df["CollateralNo"] = collateralno
        lvr_out = pd.concat([lvr_out, lvr_df], ignore_index=True)

    if not ctbc_inside_df.empty:
        ctbc_inside_df["applno"] = caseno
        ctbc_inside_df["CollateralNo"] = collateralno
        ctbc_inside_out = pd.concat([ctbc_inside_out, ctbc_inside_df], ignore_index=True)

# =============================================================================
# 6. 去除 PCSM input/output 重複列（排除 dict 欄位）
# =============================================================================

# 這些欄位內含 dict，不適合作為 drop_duplicates 的 key
dict_cols = ["H02", "T1ScoreResult", "T2ScoreResult"]
# 這些是 list 欄位，後面 dgisinput 去重時會排除
list_cols = ["ParkingSpaces"]

pcsm_input = pcsm_input.drop_duplicates(
    subset=[c for c in pcsm_input.columns if c not in dict_cols],
    ignore_index=True,
)
pcsm_output = pcsm_output.drop_duplicates(
    subset=[c for c in pcsm_output.columns if c not in dict_cols],
    ignore_index=True,
)

# 各筆案件以 applno + CollateralNo 當 key
pcsm_keys = pd.unique(
    pd.concat(
        [
            pcsm_input["applno"].astype(str) + pcsm_input["CollateralNo"].astype(str),
            pcsm_output["applno"].astype(str) + pcsm_output["CollateralNo"].astype(str),
        ],
        ignore_index=True,
    )
)

# =============================================================================
# 7. 匯出 PCSM log
# =============================================================================

pcsm_input_renamed = pcsm_input.rename(columns=clean_colname)
pcsm_output_renamed = pcsm_output.rename(columns=clean_colname)

with pd.ExcelWriter(join(datapath, f"LOG_PCSM_{Type}.xlsx")) as writer:
    pcsm_input_renamed.to_excel(writer, sheet_name="pcsm_input", index=False)
    pcsm_output_renamed.to_excel(writer, sheet_name="pcsm_output", index=False)

# =============================================================================
# 8. 匯出 Collateral / LVR / CTBC_Inside log
# =============================================================================

# dgisinput：CaseNo + CollateralNo 組 key
dgis_keys = dgisinput["CaseNo"].astype(str) + dgisinput["CollateralNo"].astype(str)
dgisinput_part = dgisinput.loc[dgis_keys.isin(pcsm_keys)].copy()

lvr_keys = lvr_out["applno"].astype(str) + lvr_out["CollateralNo"].astype(str)
lvr_out_part = lvr_out.loc[lvr_keys.isin(pcsm_keys)].copy()

ctbc_inside_keys = ctbc_inside_out["applno"].astype(str) + ctbc_inside_out["CollateralNo"].astype(str)
ctbc_inside_out_part = ctbc_inside_out.loc[ctbc_inside_keys.isin(pcsm_keys)].copy()

# dgisinput 去重時排除 list 欄位
dgisinput_part = dgisinput_part.drop_duplicates(
    subset=[c for c in dgisinput_part.columns if c not in list_cols],
    ignore_index=True,
)
lvr_out_part = lvr_out_part.drop_duplicates(ignore_index=True)
ctbc_inside_out_part = ctbc_inside_out_part.drop_duplicates(ignore_index=True)

dgisinput_renamed = dgisinput_part.rename(columns=clean_colname)
lvr_out_renamed = lvr_out_part.rename(columns=clean_colname)
ctbc_inside_out_renamed = ctbc_inside_out_part.rename(columns=clean_colname)

with pd.ExcelWriter(join(datapath, f"LOG_Collateral_{Type}.xlsx")) as writer:
    dgisinput_renamed.to_excel(writer, sheet_name="Collateral", index=False)
    lvr_out_renamed.to_excel(writer, sheet_name="LVR", index=False)
    ctbc_inside_out_renamed.to_excel(writer, sheet_name="ctbc_inside", index=False)
