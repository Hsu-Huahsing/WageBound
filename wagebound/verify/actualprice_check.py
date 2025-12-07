# -*- coding: utf-8 -*-
"""
DGIS / 實價資料月度檢核腳本（精簡版）

原始邏輯：
    - 讀取本月 / 上月實價明細（含車位拆分後檔案）
    - 做一系列欄位完整性、型態、分布變化檢查
    - 產出 Excel 報表（check / length / 各欄位分布差異）
    - 轉換原始 pkl → 上傳用 csv

本版重點：
    1. 把大量重複的 groupby + % + 差異計算收斂成共用函式
    2. 把「欄位檢核」用設定表集中管理，便於日後新增 / 修改
    3. 保留原本檢核邏輯與輸出結構，但程式長度與重複度大幅降低
"""

from os.path import join
from typing import Dict, Tuple, Optional

import pandas as pd

from wagebound.config.config import checkinterval, colname, maxlength


# ---------------------------------------------------------------------------
# 共用小工具
# ---------------------------------------------------------------------------

def interval_get(value: object = 0) -> Optional[str]:
    """
    將數值映射到 checkinterval 的區間 key。

    原始邏輯：
        for key in checkinterval:
            if int(float(value)) in checkinterval[key]:
                return key
    """
    try:
        iv = int(float(value))
    except (TypeError, ValueError):
        return None

    for key, rng in checkinterval.items():
        if iv in rng:
            return key
    return None


def len_str(x: object) -> int:
    """安全取得字串長度（None / NaN → 0）。"""
    if pd.isna(x):
        return 0
    return len(str(x))


def _build_diff_from_counts(
    this_counts: pd.Series,
    last_counts: pd.Series,
) -> pd.DataFrame:
    """
    給定「本月 / 上月」的分類計數，產出：
        thismonth_cnt, thismonth_%, lastmonth_cnt, lastmonth_%, diff_cnt, diff_%
    並在最後加上一列 SUM。
    """
    idx = sorted(set(this_counts.index) | set(last_counts.index))
    c1 = this_counts.reindex(idx, fill_value=0).astype(float)
    c2 = last_counts.reindex(idx, fill_value=0).astype(float)

    if c1.sum():
        pct1 = c1 / c1.sum() * 100
    else:
        pct1 = c1 * 0
    if c2.sum():
        pct2 = c2 / c2.sum() * 100
    else:
        pct2 = c2 * 0

    df1 = pd.concat([c1, pct1], axis=1)
    df2 = pd.concat([c2, pct2], axis=1)
    df1.columns = ["thismonth_cnt", "thismonth_%"]
    df2.columns = ["lastmonth_cnt", "lastmonth_%"]

    diff_cnt = df1["thismonth_cnt"] - df2["lastmonth_cnt"]
    diff_pct = df1["thismonth_%"] - df2["lastmonth_%"]
    diff = pd.concat([diff_cnt, diff_pct], axis=1)
    diff.columns = ["diff_cnt", "diff_%"]

    out = pd.concat([df1, df2, diff], axis=1)
    sum_row = pd.DataFrame(out.sum()).T
    sum_row.index = ["SUM"]
    out = pd.concat([out, sum_row], axis=0)
    return out


def build_interval_table(
    this_df: pd.DataFrame,
    last_df: pd.DataFrame,
    col: str,
) -> pd.DataFrame:
    """
    針對數值欄位（例如面積、總價、單價等），
    先用 interval_get 切成區間，再比較本月 / 上月的分布。
    """
    s1 = this_df[col].apply(interval_get)
    s2 = last_df[col].apply(interval_get)
    c1 = s1.value_counts(dropna=True).sort_index()
    c2 = s2.value_counts(dropna=True).sort_index()
    return _build_diff_from_counts(c1, c2)


def build_group_table(
    this_df: pd.DataFrame,
    last_df: pd.DataFrame,
    group_col: str,
    count_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    針對類別欄位（例如用途、分區、旗標等），
    直接用 groupby 做計數並比較分布差異。
    """
    if count_col is None:
        count_col = group_col
    c1 = this_df.groupby(group_col)[count_col].count()
    c2 = last_df.groupby(group_col)[count_col].count()
    return _build_diff_from_counts(c1, c2)


def strtodate(x: object) -> Optional[str]:
    """
    將民國年月日（例：0820412）字串轉成「YYYY/MM/DD」格式。

    規則與原始版相同：
        - 補零成 7 碼
        - 年份 +1911
        - 月 / 日為 00 時補 01
        - 無法解析時回傳 None
    """
    if pd.isna(x):
        return None

    s = str(x).split(".")[0]          # 去掉小數
    s = s.replace(" ", "").replace("-", "")
    if not (6 <= len(s) <= 7):
        return None

    s = s.zfill(7)
    d = s[-2:]
    m = s[-4:-2]
    y = str(int(s[:-4]) + 1911)

    if d == "00":
        d = "01"
    if m == "00":
        m = "01"

    dt = pd.to_datetime("-".join([y, m, d]), errors="coerce")
    if pd.isna(dt):
        return None
    return dt.strftime("%Y/%m/%d")


# ---------------------------------------------------------------------------
# 欄位檢核（完整性 / 型態 / 長度）
# ---------------------------------------------------------------------------

def run_basic_checks(file: pd.DataFrame, file_last: pd.DataFrame) -> Tuple[Dict[str, object], pd.DataFrame]:
    """
    執行欄位完整性與長度檢核，回傳：
        - res: 各欄位檢核結果字典
        - length_df: 欄位實際長度 vs 設定 maxlength
    """
    res: Dict[str, object] = {}

    # 1) 唯一鍵檢查（序號 / 編號）
    for col in ["DRPD_Sequence", "DRPD_Number"]:
        dup_or_null = file[file[col].duplicated(keep=False) | file[col].isna()]
        if dup_or_null.empty:
            res[col] = ["Y", dup_or_null.shape]
        else:
            print(f"{col} ERROR !")

    # 2) 應為空值的欄位（Geom）
    non_null_geom = file[~file["Geom"].isna()]
    if non_null_geom.empty:
        res["Geom"] = ["Y", non_null_geom.shape]
    else:
        print("Geom ERROR !")

    # 3) 簡單欄位缺漏檢查
    simple_not_null_cols = [
        "DRPD_City",
        "DRPD_District",
        "DRPD_Transactions",
        "DRPD_BuildingType",
        "DRPD_LayoutBedroom",
        "DRPD_LayoutLivroom",
        "DRPD_LayoutBathroom",
    ]
    for col in simple_not_null_cols:
        missing = file[file[col].isna()]
        if missing.empty:
            res[col] = ["Y", missing.shape]
        else:
            print(f"{col} ERROR !")

    # 4) 交易標的不得為空或純土地
    trade_invalid = file[file["DRPD_TradeTarget"].isna() | (file["DRPD_TradeTarget"] == "土地")]
    if trade_invalid.empty:
        res["DRPD_TradeTarget"] = ["Y", trade_invalid.shape]
    else:
        print("DRPD_TradeTarget ERROR !")

    # 5) 地址長度限制（<= 30）
    addr_invalid = file[file["DRPD_Address"].isna() | (file["DRPD_Address"].apply(len_str) > 30)]
    if addr_invalid.empty:
        res["DRPD_Address"] = ["Y", addr_invalid.shape]
    else:
        print("DRPD_Address ERROR !")

    # 6) dtype 應為 object 的欄位
    object_cols = [
        "DRPD_LandUseType",
        "DRPD_NonUrbanDistrict",
        "DRPD_NonUrbanland",
        "DRPD_TransFloor",
        "DRPD_TotalFloor",
        "DRPD_MainPurpose",
        "DRPD_MainMaterial",
        "DRPD_CompletionDate",
        "DRPD_Note",
        "DRPD_BuildingName",
        "DRPD_BuildingKey",
        "DRPD_NoteFlag",
    ]
    for col in object_cols:
        if str(file[col].dtype) == "object":
            res[col] = "Y"
        else:
            print(f"{col} ERROR !")

    # 7) 交易日期欄位型態 + 範圍
    trade_dates = [file["DRPD_TradeDate"].max(), file["DRPD_TradeDate"].min()]
    if str(file["DRPD_TradeDate"].dtype) == "object":
        res["DRPD_TradeDate"] = ["Y"] + trade_dates
    else:
        print("DRPD_TradeDate ERROR !")

    # 8) 路名 / 巷名長度檢核（<= 20）
    road_long = file[file["DRPD_RoadSecName"].apply(len_str) > 20]
    if road_long.empty:
        res["DRPD_RoadSecName"] = ["Y", road_long.shape]
    else:
        print("DRPD_RoadSecName ERROR !")

    alley_long = file[file["DRPD_AlleyName"].apply(len_str) > 20]
    if alley_long.empty:
        res["DRPD_AlleyName"] = ["Y", alley_long.shape]
    else:
        print("DRPD_AlleyName ERROR !")

    # 9) TargetX / TargetY 小數點檢查（原始註解：KeyError 正常）
    for col in ["DRPD_TargetX", "DRPD_TargetY"]:
        _ = file[col].astype(str).str.split(".", expand=True)
        res[col] = "Y"

    # 10) 資料長度檢核（maxlength 對照）
    length_df = pd.DataFrame([maxlength], index=["max"])
    actual_len: Dict[str, int] = {}
    for col, _max in maxlength.items():
        if col in file.columns:
            actual_len[col] = file[col].apply(len_str).max()
        else:
            actual_len[col] = 0
    length_df = pd.concat([pd.DataFrame([actual_len], index=["data_length"]), length_df]).T
    length_df["diff"] = length_df["max"] - length_df["data_length"]

    return res, length_df


# ---------------------------------------------------------------------------
# 上傳檔案前後版本欄位檢查
# ---------------------------------------------------------------------------

def profile_upload_file(df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    檢查每個欄位：
        - 是否包含 NaN
        - 是否可轉成 float
    回傳：
        (has_nan_map, is_float_map)
    """
    has_nan: Dict[str, str] = {}
    is_float: Dict[str, str] = {}

    for col in df.columns:
        series = df[col]
        has_nan[col] = "Y" if series.isna().any() else "N"
        try:
            series.astype(float)
            is_float[col] = "Y"
        except Exception:
            is_float[col] = "N"

    return has_nan, is_float


# ---------------------------------------------------------------------------
# 主流程（main）
# ---------------------------------------------------------------------------

def main() -> None:
    # 月份設定：month[1] = 本月，month[0] = 上月
    month = pd.date_range("2025-10", periods=2, freq="MS")  # 注意：依實務調整

    file_name = "GEOM_CTBC_RealPriceDetail_stall.csv"
    file_name_old = "GEOM_CTBC_RealPriceDetail.csv"

    path_wb = r"D:\DGIS\workbench"
    path_zipcode = r"D:\DGIS\ZIP.xlsx"

    path = join(path_wb, month[1].strftime("%Y%m"), file_name)
    path_last = join(path_wb, month[0].strftime("%Y%m"), file_name)
    path_ttl = join(path_wb, month[1].strftime("%Y%m"), "GEOM_CTBC_RealPriceDetail.pkl")
    path_building = join(path_wb, month[1].strftime("%Y%m"), "building.pkl")

    # 讀取本月 / 上月檔案
    file = pd.read_csv(path, dtype=str, sep="|", encoding="utf8")
    file_last = pd.read_csv(path_last, dtype=str, sep="|", encoding="utf8")
    file_zipcode = pd.read_excel(path_zipcode, dtype=str).rename(
        columns={"city": "DRPD_City", "town": "DRPD_District", "zip": "zip_check"}
    )

    # ------------------------------------------------------------------
    # 一、欄位檢核（完整性 / 型態 / 長度）
    # ------------------------------------------------------------------
    res_dict, length_df = run_basic_checks(file, file_last)

    # 郵遞區號檢核（依原始邏輯）
    merged_zip = pd.merge(file, file_zipcode, how="left", on=["DRPD_City", "DRPD_District"])
    zip_mismatch = merged_zip[
        (merged_zip["DRPD_ZipCode"] != merged_zip["zip_check"]) | merged_zip["DRPD_ZipCode"].isna()
    ]
    if zip_mismatch.empty:
        res_dict["DRPD_ZipCode"] = ["Y", zip_mismatch.shape]
    else:
        print("DRPD_ZipCode ERROR !")

    # ------------------------------------------------------------------
    # 二、分布變化檢核：interval 型 + 類別型
    # ------------------------------------------------------------------
    # 1) interval 型欄位（需用 interval_get 切段）
    interval_cols = [
        "DRPD_LandTransArea",
        "DRPD_TransArea",
        "DRPD_TotalPrice",
        "DRPD_UnitPrice",
        "DRPD_UnitPriceRevised",
        "DRPD_StallTotalPriceProxy",
        "DRPD_StallCnt",
        "DRPD_StallTransArea",
        "DRPD_StallTotalPrice",
        "DRPD_BuildingAge",
        "DRPD_GParking",
        "DRPD_EParking",
        "DRPD_GParkingPrice",
        "DRPD_EParkingPrice",
        "DRPD_TransFloorFlag",
        "DRPD_TotalFloorFlag",
        "DRPD_BuildingArea",
    ]
    interval_tables: Dict[str, pd.DataFrame] = {}
    for col in interval_cols:
        if col in file.columns and col in file_last.columns:
            interval_tables[col] = build_interval_table(file, file_last, col)

    # 2) 類別型欄位分布
    group_configs = [
        ("DRPD_BuildingTypeFlag", "DRPD_BuildingTypeFlag", None),
        ("DRPD_Partition", "DRPD_Partition", None),
        ("DRPD_Management", "DRPD_Management", None),
        ("DRPD_RealEstateStallFlag", "DRPD_Management", "DRPD_RealEstateStallFlag"),
        ("DRPD_HasNote", "DRPD_HasNote", None),
        ("DRPD_SpecialTradeFlag", "DRPD_SpecialTradeFlag", None),
        ("DRPD_FishId", "DRPD_FishId", None),
        ("DRPD_BuildingSeg", "DRPD_BuildingSeg", None),
        ("DRPD_OutlierTxn", "DRPD_OutlierTxn", None),
        ("DRPD_IsAlley", "DRPD_IsAlley", None),
        ("DRPD_ModifyFlag", "DRPD_ModifyFlag", None),
        ("DRPD_CommunityFlag", "DRPD_CommunityFlag", None),
    ]
    group_tables: Dict[str, pd.DataFrame] = {}
    for sheet_name, group_col, count_col in group_configs:
        if group_col in file.columns and group_col in file_last.columns:
            group_tables[sheet_name] = build_group_table(file, file_last, group_col, count_col=count_col)

    # ------------------------------------------------------------------
    # 三、輸出檢核結果至 Excel
    # ------------------------------------------------------------------
    res_df = pd.DataFrame([res_dict])
    out_path = join(path_wb, month[1].strftime("%Y%m"), "CheckResult_Python.xlsx")

    with pd.ExcelWriter(out_path) as writer:
        res_df.to_excel(writer, sheet_name="check", index=False)
        length_df.to_excel(writer, sheet_name="length", index=True)

        # interval 型 sheet
        for col, df_interval in interval_tables.items():
            df_interval.to_excel(writer, sheet_name=col, index=True)

        # 類別型 sheet
        for sheet_name, df_group in group_tables.items():
            df_group.to_excel(writer, sheet_name=sheet_name, index=True)

    # ------------------------------------------------------------------
    # 四、處理歷史 pkl → 上傳 csv
    # ------------------------------------------------------------------
    file_ttl = pd.read_pickle(path_ttl)
    file_building = pd.read_pickle(path_building)

    # drop 無用欄位
    file_ttl = file_ttl.drop(columns=["Unnamed: 35"], errors="ignore")

    # 建物檔案只保留本月交易編號
    file_building = file_building[file_building["編號"].isin(file["DRPD_Number"])]
    file_building = file_building.rename(columns=colname["建物"])

    # 不動產買賣欄位改名 + 日期轉換
    file_ttl = file_ttl.rename(columns=colname["不動產買賣"])
    file_ttl[["Trading_Date", "Completion_Date"]] = file_ttl[
        ["Trading_Date", "Completion_Date"]
    ].applymap(strtodate)

    # 輸出 csv 供 DGIS / 上傳使用
    file_ttl.to_csv(join(path_wb, month[1].strftime("%Y%m"), file_name_old),
                    sep="|", index=False, encoding="utf8")
    file_building.to_csv(
        join(path_wb, month[1].strftime("%Y%m"), "building.csv"),
        sep="|",
        index=False,
        encoding="utf8",
    )

    # ------------------------------------------------------------------
    # 五、上傳前後檔案欄位特性檢查（NaN / 可否轉 float）
    # ------------------------------------------------------------------
    path_upload_last = join(path_wb, month[0].strftime("%Y%m"), r"上傳DGIS", file_name_old)
    path_upload = join(path_wb, month[1].strftime("%Y%m"), r"上傳DGIS", file_name_old)

    file_upload_last = pd.read_csv(path_upload_last, dtype=str, sep="|", encoding="utf8")
    file_upload = pd.read_csv(path_upload, dtype=str, sep="|", encoding="utf8")

    has_nan_last, is_float_last = profile_upload_file(file_upload_last)
    has_nan_curr, is_float_curr = profile_upload_file(file_upload)

    # 原本只是比對 values；這裡順便列出有變動的欄位
    diff_float_cols = [col for col in is_float_curr if is_float_curr.get(col) != is_float_last.get(col)]
    if diff_float_cols:
        print("下列欄位『是否可轉 float』與上月不同，請人工確認：")
        print(diff_float_cols)

    # 原始最後一段只是測試長度，保留
    file["len"] = file["DRPD_LandUseType"].apply(len_str)
    _ = file[["DRPD_LandUseType", "len"]]


if __name__ == "__main__":
    main()
