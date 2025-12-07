# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 09:24:36 2024

@author: Z00051711

用途：
1. 讀取單筆相似度 JSON（CollateralData + Result）
2. 展開 CompareCase → CTBC_Inside 與 LVR，整理成 3 個 sheet
3. 每檔 JSON 輸出一份「相似度分析{檔名}.xlsx」
4. 再將所有「相似度分析*.xlsx」統整成「相似度分析_統整.xlsx」
"""

import json
import pandas as pd
from os.path import join
from ctbc_project.config import comparecase_clean, comparecase_select
from StevenTricks.fileop import PathWalk_df


# 欄位名稱清理對照
CLEAN_COLNAME = {
    "SimilarityFlag": "Similarityflag",
}

# 實價資料：用來補上 DRPD_SpecialTradeFlag
ACTUALPRICE_PATH = r"D:\DGIS\workbench\202407\GEOM_CTBC_RealPriceDetail_stall.csv"
TEMP_PATH = r"C:\Users\z00188600\Desktop"

# 這裡可以一次放多個檔名，例如 ["LV1", "LV2", "LV3"]
CASE_FILES = ["LV3"]


# ----------------------------------------------------------------------
# 小工具
# ----------------------------------------------------------------------
def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """統一欄位命名規則。"""
    return df.rename(columns=CLEAN_COLNAME)


def load_actualprice(path: str) -> pd.DataFrame:
    """讀取實價明細，只保留後面要用到的欄位。"""
    df = pd.read_csv(path, sep="|")
    return df[["DRPD_Number", "DRPD_SpecialTradeFlag"]].rename(
        columns={"DRPD_Number": "Id"}
    )


# ----------------------------------------------------------------------
# 處理單一 JSON 檔案
# ----------------------------------------------------------------------
def process_case_json(case_name: str,
                      temp_path: str,
                      actualprice: pd.DataFrame) -> None:
    """讀取單一 JSON 檔案並輸出相似度分析 Excel。"""

    json_path = join(temp_path, f"{case_name}.json")
    with open(json_path, encoding="utf-8") as f:
        temp_data = json.load(f)

    # 1. 拆出 input / output
    upload_dict = temp_data["CollateralData"]
    output_dict = temp_data["Result"]

    appnbr = upload_dict["CaseNo"]
    colnbr = str(upload_dict["CollateralNo"])

    # 2. CompareCase 清理
    raw_comparecase = output_dict.pop("CompareCase")
    comparecase = comparecase_select(raw_comparecase)
    output_dict["CompareCase"] = comparecase_clean(
        comparecase,
        AppNbr=appnbr,
        CollNbr=colnbr,
    )

    # 3. 建成 DataFrame
    collateral = pd.DataFrame([upload_dict])
    ctbc = pd.DataFrame(output_dict["CompareCase"]["CTBC_Inside"])
    lvr = pd.DataFrame(output_dict["CompareCase"]["LVR"])

    # 4. 欄位名稱清理
    collateral = rename_columns(collateral)
    ctbc = rename_columns(ctbc)
    lvr = rename_columns(lvr)

    # 5. 接上實價的特殊交易旗標
    lvr = lvr.merge(actualprice, on="Id", how="left")

    # 6. 輸出 Excel（每個 JSON 一份）
    out_path = join(temp_path, f"相似度分析{case_name}.xlsx")
    with pd.ExcelWriter(out_path) as writer:
        collateral.to_excel(writer, sheet_name="collateral", index=False)
        ctbc.to_excel(writer, sheet_name="ctbc_inside", index=False)
        lvr.to_excel(writer, sheet_name="lvr", index=False)

    print(f"完成：ApplNo={appnbr}, File={case_name}")


# ----------------------------------------------------------------------
# 統整所有「相似度分析*.xlsx」
# ----------------------------------------------------------------------
def aggregate_similarity_excels(temp_path: str,
                                include_keyword: str = "相似度分析",
                                exclude_keywords=None) -> None:
    """將所有相似度分析 Excel 彙總成一份統整檔。"""
    if exclude_keywords is None:
        exclude_keywords = [".zip", "統整"]

    df_path = PathWalk_df(
        temp_path,
        fileinclude=[include_keyword],
        fileexclude=exclude_keywords,
    )

    collateral_list = []
    ctbc_list = []
    lvr_list = []

    for path_file in df_path["path"]:
        sheets = pd.read_excel(path_file, sheet_name=None)
        collateral_list.append(sheets["collateral"])
        ctbc_list.append(sheets["ctbc_inside"])
        lvr_list.append(sheets["lvr"])

    if not collateral_list:
        print("找不到任何『相似度分析*.xlsx』檔案，略過統整。")
        return

    collateral = pd.concat(collateral_list, ignore_index=True)
    case_ctbc = pd.concat(ctbc_list, ignore_index=True)
    case_lvr = pd.concat(lvr_list, ignore_index=True)

    out_path = join(temp_path, "相似度分析_統整.xlsx")
    with pd.ExcelWriter(out_path) as writer:
        collateral.to_excel(writer, sheet_name="collateral", index=False)
        case_ctbc.to_excel(writer, sheet_name="ctbc_inside", index=False)
        case_lvr.to_excel(writer, sheet_name="lvr", index=False)

    print(f"統整完成：{out_path}")


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 實價資料（只讀一次，後面每個 JSON 共用）
    actualprice_df = load_actualprice(ACTUALPRICE_PATH)

    # 逐檔 JSON 處理
    for case in CASE_FILES:
        process_case_json(case_name=case,
                          temp_path=TEMP_PATH,
                          actualprice=actualprice_df)

    # 統整所有相似度分析結果
    aggregate_similarity_excels(TEMP_PATH)
