# -*- coding: utf-8 -*-
"""
LOG 解譯工具
------------

用途：
    - 讀取指定路徑下的 LOG .txt 檔
    - 解析 Input / Output JSON
    - 拆解為：
        * Collateral（dgisinput）
        * LVR
        * CTBC_Inside
        * PCSM Input / Output
        * Result（含 ResultFile 攤平）
    - 輸出：
        * LOG_Collateral_uat.xlsx  （Collateral / LVR / ctbc_inside）
        * LOG_PCSM_uat.xlsx        （pcsm_input / pcsm_output / result）
"""

import ast
import json
from os.path import join

import pandas as pd

from wagebound.config.config import comparecase_select, clean_colname
from StevenTricks.io.file_utils import PathWalk_df

# ----------------------------------------------------------------------
# 設定區：路徑與字串清理
# ----------------------------------------------------------------------

# 把 .txt 丟到這個路徑底下再執行本程式
BASE_LOG_PATH = (
    r"\\w80770616\個金風險政策部\99.各科\01.擔保\05.房貸PCO\驗證報告"
    r"\202511_HPM2透天及策略優化\上線日"
)

# Output JSON 特殊字串修正
REPLACE_WORDS = [
    ('A"MORE社區', "A'MORE社區"),
    ('C"EST LA VIE', "C'EST LA VIE"),
    ("4'33''", "4分33秒"),
    ('4"33""', "4分33秒"),
]


# ----------------------------------------------------------------------
# 工具函式
# ----------------------------------------------------------------------


def dict_to_df(dict_list) -> pd.DataFrame:
    """
    將 comparecase["LVR"] / ["CTBC_Inside"] 這種結構：
        [{"properties": {...}}, {"properties": {...}}, ...]
    攤平成 DataFrame。
    """
    if not dict_list:
        return pd.DataFrame()
    return pd.DataFrame([item["properties"] for item in dict_list])


def rename_clean(df: pd.DataFrame) -> pd.DataFrame:
    """套用 clean_colname 映射，若 df 為空直接回傳。"""
    if df is None or df.empty:
        return df
    return df.rename(columns=clean_colname)


def read_log_lines(path: str) -> list[str]:
    """
    讀取單一 LOG 檔，回傳「已去換行」的字串列表。
    以 utf-8 為主，遇到異常字元忽略。
    """
    with open(path, "rb") as f:
        return [line.decode("utf-8", errors="ignore").strip() for line in f.readlines()]


def parse_single_log(path: str) -> dict[str, pd.DataFrame]:
    """
    解析單一 LOG 檔，回傳一組 DataFrame 字典：
        {
            "dgisinput": df,
            "lvr_out": df,
            "ctbc_inside_out": df,
            "pcsm_input": df,
            "pcsm_output": df,
            "result": df,
        }
    """
    log_list = read_log_lines(path)
    if len(log_list) < 6:
        # 格式異常，直接略過
        return {
            "dgisinput": pd.DataFrame(),
            "lvr_out": pd.DataFrame(),
            "ctbc_inside_out": pd.DataFrame(),
            "pcsm_input": pd.DataFrame(),
            "pcsm_output": pd.DataFrame(),
            "result": pd.DataFrame(),
        }

    # 基本頭三行：ApplNo / ApplNoB / GuaraNo
    appl_no = log_list[0].split(":")[-1].strip()
    # appl_no_b = log_list[1].split(":")[-1].strip()  # 若未使用，可忽略
    guara_no = log_list[2].split(":")[-1].strip()

    # Input：第 4 行，去掉前 6 個字元（沿用原本邏輯）
    input_raw = log_list[3][6:]
    input_json = ast.literal_eval(input_raw)

    # Output：第 6 行，去掉前 7 個字元，再把單引號改成雙引號
    output_raw = log_list[5][7:].replace("'", '"')
    for old, new in REPLACE_WORDS:
        output_raw = output_raw.replace(old, new)
    output_json = json.loads(output_raw)

    # -----------------------------
    # Collateral + Location
    # -----------------------------
    dgisinput = pd.concat(
        [
            pd.DataFrame([input_json.get("CollateralData", {})]),
            pd.DataFrame([input_json.get("Location", {})]),
        ],
        axis=1,
    )
    dgisinput["applno"] = appl_no
    dgisinput["ZipCode"] = output_json["Result"].get("ZipCode")

    # -----------------------------
    # CompareCase：LVR / CTBC_Inside
    # -----------------------------
    comparecase = comparecase_select(output_json["Result"]["CompareCase"])
    lvr_out = dict_to_df(comparecase.get("LVR", []))
    ctbc_inside_out = dict_to_df(comparecase.get("CTBC_Inside", []))

    for df in (lvr_out, ctbc_inside_out):
        if not df.empty:
            df["applno"] = appl_no
            df["CollateralNo"] = guara_no

    # -----------------------------
    # Result：含 ResultFile 攤平
    # -----------------------------
    result_dict = output_json.get("Result", {})
    result_file_dict = result_dict.get("ResultFile", {})

    result = pd.DataFrame([result_dict]).drop(columns=["ResultFile"], errors="ignore")
    if result_file_dict:
        result = pd.concat([result, pd.DataFrame([result_file_dict])], axis=1)

    result["applno"] = appl_no
    result["CollateralNo"] = guara_no

    # -----------------------------
    # PerformanceStatistic：PCSM Input / Output
    # -----------------------------
    pcsm_input = pd.DataFrame()
    pcsm_output = pd.DataFrame()

    perf_stat = output_json.get("PerformanceStatistic")
    if perf_stat is not None:
        if "PCSMINPUT" in perf_stat:
            pcsm_input = pd.DataFrame([perf_stat["PCSMINPUT"]])
            pcsm_input["applno"] = appl_no

        if "PCSMOUTPUT" in perf_stat:
            pcsm_output = pd.DataFrame([perf_stat["PCSMOUTPUT"]])
            pcsm_output["applno"] = appl_no
            pcsm_output["CollateralNo"] = guara_no

    # -----------------------------
    # 欄位名稱清理
    # -----------------------------
    dgisinput = rename_clean(dgisinput)
    lvr_out = rename_clean(lvr_out)
    ctbc_inside_out = rename_clean(ctbc_inside_out)
    pcsm_input = rename_clean(pcsm_input)
    pcsm_output = rename_clean(pcsm_output)
    result = rename_clean(result)

    return {
        "dgisinput": dgisinput,
        "lvr_out": lvr_out,
        "ctbc_inside_out": ctbc_inside_out,
        "pcsm_input": pcsm_input,
        "pcsm_output": pcsm_output,
        "result": result,
    }


# ----------------------------------------------------------------------
# 主程式
# ----------------------------------------------------------------------


def main(base_path: str = BASE_LOG_PATH) -> None:
    # 掃描所有 .txt LOG 檔
    df_path = PathWalk_df(base_path, fileinclude=[".txt"])

    all_dfs = {
        "dgisinput": [],
        "lvr_out": [],
        "ctbc_inside_out": [],
        "pcsm_input": [],
        "pcsm_output": [],
        "result": [],
    }

    for path in df_path["path"]:
        parsed = parse_single_log(path)
        for key, df in parsed.items():
            if df is not None and not df.empty:
                all_dfs[key].append(df)

    # 將各批次結果 concat 起來
    def _concat(key: str) -> pd.DataFrame:
        return (
            pd.concat(all_dfs[key], ignore_index=True)
            if all_dfs[key]
            else pd.DataFrame()
        )

    dgisinput_excel = _concat("dgisinput")
    lvr_out_excel = _concat("lvr_out")
    ctbc_inside_out_excel = _concat("ctbc_inside_out")
    pcsm_input_excel = _concat("pcsm_input")
    pcsm_output_excel = _concat("pcsm_output")
    result_excel = _concat("result")

    # -----------------------------
    # 輸出 Excel
    # -----------------------------
    # Collateral + CompareCase 結果
    with pd.ExcelWriter(join(base_path, "LOG_Collateral_uat.xlsx")) as writer:
        dgisinput_excel.to_excel(writer, sheet_name="Collateral", index=False)
        lvr_out_excel.to_excel(writer, sheet_name="LVR", index=False)
        ctbc_inside_out_excel.to_excel(writer, sheet_name="ctbc_inside", index=False)

    # PCSM Input / Output / Result
    with pd.ExcelWriter(join(base_path, "LOG_PCSM_uat.xlsx")) as writer:
        pcsm_input_excel.to_excel(writer, sheet_name="pcsm_input", index=False)
        pcsm_output_excel.to_excel(writer, sheet_name="pcsm_output", index=False)
        result_excel.to_excel(writer, sheet_name="result", index=False)


if __name__ == "__main__":
    main()
