# -*- coding: utf-8 -*-
"""
DGIS 實價登錄清理流程：
1. 讀原始 Excel
2. rename / drop 欄位
3. 日期轉換、過濾標的
4. 算建物年齡、建物型態分段、坪數/單價轉換
5. merge 郵遞區號
6. 算 FishID
7. 匯出送 DGIS 檔案 + 加工回寫檔檢查

原始版本：2023-10-19
整理優化版：2025-12-07
"""

from copy import deepcopy
from os import makedirs, walk
from os.path import abspath, dirname, isfile, join, pardir, samefile

import datetime as dt
import pickle

import pandas as pd
from numpy import floor

from wagebound.config.config_dgis import (
    DGIS_RAW_ROOT,
    DGIS_WB_ROOT,
    DATE_START,
    DATE_PERIODS,
    PATH_XY,
    PATH_ZIP,
    FILE_TOTAL,
    FILE_SEND,
    EXCEL_EXT,
    COLNAME,
    DROPCOL,
    CITYNAME,
    DGISKEY,
    DGISKEY_LIST,
)

# ----------------------------------------------------------------------
# 工具函式區
# ----------------------------------------------------------------------


def picklesave(data, path: str):
    """存 pickle（確保資料夾存在）"""
    makedirs(abspath(dirname(path)), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(data, f)


def pickleload(path: str):
    """讀 pickle"""
    with open(path, "rb") as f:
        return pickle.load(f)


def pathlevel(left: str, right: str) -> int:
    """計算 right 相對 left 的層級差"""
    if isfile(right):
        right = abspath(join(right, pardir))
    if len(left) > len(right):
        return 0
    level = 0
    while not samefile(left, right):
        right = abspath(join(right, pardir))
        level += 1
    return level


def PathWalk_df(
    path: str,
    dirinclude=None,
    direxclude=None,
    fileexclude=None,
    fileinclude=None,
    level=None,
) -> pd.DataFrame:
    """
    掃描資料夾，回傳 file/path/level DataFrame
    - dirinclude: 目錄路徑要包含的字串（list）
    - direxclude: 要排除的目錄（list）
    - fileinclude: 檔名要包含的 pattern（list，例如 ['.xls']）
    - fileexclude: 要排除的 pattern（list）
    - level: 最大層級
    """
    dirinclude = dirinclude or []
    direxclude = direxclude or []
    fileexclude = fileexclude or []
    fileinclude = fileinclude or []

    rows = []
    for _path, _dirs, _files in walk(path):
        if not _dirs and not _files:
            rows.append([None, path])
        for f in _files:
            rows.append([f, join(_path, f)])

    res = pd.DataFrame(rows, columns=["file", "path"])
    res["level"] = res["path"].map(lambda x: pathlevel(path, x))

    if level is not None:
        res = res.loc[res["level"] <= level]

    if dirinclude:
        res = res.loc[res["path"].str.contains("\\|\\".join(dirinclude), na=False)]

    if direxclude:
        res = res.loc[
            ~(res["path"].str.contains("\\|\\".join(direxclude), na=True))
        ]

    if fileinclude:
        res = res.loc[res["file"].str.contains("|".join(fileinclude), na=False)]

    if fileexclude:
        res = res.loc[~res["file"].str.contains("|".join(fileexclude), na=True)]

    return res.reset_index(drop=True)


def strtodate(x):
    """
    將 ROC 7 碼（例如 0820412）轉成 'YYYY/MM/DD'
    - 允許有小數、空白、'-' 等雜訊
    """
    if pd.isna(x):
        return None

    x = str(x).split(".")[0]
    x = x.replace(" ", "").replace("-", "")

    if 6 <= len(x) <= 7:
        x = x.zfill(7)
    else:
        return None

    d = x[-2:]
    m = x[-4:-2]
    y = str(int(x[:-4]) + 1911)

    if d == "00":
        d = "01"
    if m == "00":
        m = "01"

    res = pd.to_datetime("-".join([y, m, d]), errors="coerce")
    if pd.isna(res):
        return None
    return res.strftime("%Y/%m/%d")


# FishID 相關：預先載入座標對應表
DATA_XY = pd.read_excel(PATH_XY, dtype=str)


def fishID_get(source: pd.DataFrame, col_x: str, col_y: str) -> pd.DataFrame:
    """
    依 X/Y 座標計算 FishID，並回填到 source['DRPD_FishId']
    """
    lis = list(range(100, 1100, 200))

    x = (pd.to_numeric(source[col_x]) * 0.001 - floor(pd.to_numeric(source[col_x]) * 0.001)) * 1000
    y = (pd.to_numeric(source[col_y]) * 0.001 - floor(pd.to_numeric(source[col_y]) * 0.001)) * 1000

    x[x < 100] = 100
    y[y < 100] = 100

    for n in [0, 1, 2, 3]:
        mid = (lis[n] + lis[n + 1]) / 2
        x[x.between(lis[n], lis[n + 1], inclusive="right") & (x > mid)] = lis[n + 1]
        x[x.between(lis[n], lis[n + 1], inclusive="right") & (x <= mid)] = lis[n]
        y[y.between(lis[n], lis[n + 1], inclusive="right") & (y > mid)] = lis[n + 1]
        y[y.between(lis[n], lis[n + 1], inclusive="right") & (y <= mid)] = lis[n]

    x[x > 900] = 900
    y[y > 900] = 900

    x = floor(pd.to_numeric(source[col_x]) * 0.001) * 1000 + x
    y = floor(pd.to_numeric(source[col_y]) * 0.001) * 1000 + y

    df_temp = pd.DataFrame(
        {
            "P_X": x.map(lambda v: str(v).split(".")[0]),
            "P_Y": y.map(lambda v: str(v).split(".")[0]),
        }
    )

    df_temp = df_temp.merge(DATA_XY, on=["P_X", "P_Y"], how="left").fillna("0")
    source["DRPD_FishId"] = df_temp["FishID"]

    return source


# ----------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------


def main():
    # 1. 決定月份區間與路徑
    d = pd.date_range(start=DATE_START, periods=DATE_PERIODS, freq="MS")
    month_str = d.max().strftime("%Y%m")

    path_raw = join(DGIS_RAW_ROOT, month_str)
    path_wb = join(DGIS_WB_ROOT, month_str)
    path_processing = join(path_wb, "processing")

    for p in [path_raw, path_wb, path_processing]:
        makedirs(p, exist_ok=True)

    # 2. 讀所有縣市 Excel
    excel_paths = PathWalk_df(path_raw, fileinclude=[EXCEL_EXT], level=0)
    excel_paths = excel_paths.loc[excel_paths["level"] == 0, :]
    res = {}

    for file_path in excel_paths["path"]:
        file_dict = pd.read_excel(file_path, sheet_name=None)

        # 找出城市代碼
        city = None
        for vol in CITYNAME:
            if f"list_{vol.lower()}" in file_path:
                city = CITYNAME[vol]
                break

        # 清理每一個 sheet
        for key, df in file_dict.items():
            newkey = key.split("_")[0]
            if newkey not in ["建物", "不動產買賣"]:
                continue

            # drop 雜訊欄
            df = df.drop(columns=["Unnamed: 35", "Unnamed: 0"], errors="ignore")

            # rename
            if newkey in COLNAME:
                df = df.rename(columns=COLNAME[newkey])

            # 針對「不動產買賣」再 drop 一些欄
            if newkey in DROPCOL:
                df = df.drop(columns=DROPCOL[newkey], errors="ignore")

            if not df.empty:
                df.insert(0, "City", city)

                # 建物完成日期轉成整數字串（例如 0820412）
                if newkey == "建物" and "Building_Completion_Date" in df:
                    temp = (
                        df["Building_Completion_Date"]
                        .astype(str)
                        .str.split("年|月|日", expand=True)
                        .rename(columns={0: "year", 1: "month", 2: "day"})
                    )
                    temp["year"] = temp["year"].str.zfill(3)
                    temp["month"] = temp["month"].str.zfill(2)
                    temp["day"] = temp["day"].str.zfill(2)
                    df["Building_Completion_Date_v"] = (
                        temp["year"] + temp["month"] + temp["day"]
                    )

            if newkey not in res:
                res[newkey] = df
            else:
                res[newkey] = pd.concat([res[newkey], df], ignore_index=True)

    # 3. 只保留「不動產買賣」，存原始檔
    realestate_raw = res["不動產買賣"].copy()
    picklesave(realestate_raw, join(path_wb, "realestate_original"))

    data = deepcopy(realestate_raw)
    del res, realestate_raw

    # 4. 轉換日期欄位
    data[["Trading_Date", "Completion_Date"]] = data[
        ["Trading_Date", "Completion_Date"]
    ].applymap(strtodate)
    picklesave(data, join(path_wb, "realestate_date"))

    # 5. 篩選標的種類與建物型態
    data = data.loc[data["Trading_Target"] != "土地", :]
    data = data.loc[~data["Building_Type"].isin(["工廠", "倉庫", "農舍"]), :]
    data = data.loc[~data["Completion_Date"].isna(), :]

    # Trading_Date -> datetime
    data["Trading_Date"] = pd.to_datetime(data["Trading_Date"], errors="coerce")

    # 限制在指定月份區間內
    data = data.loc[data["Trading_Date"].between(d.min(), d.max(), inclusive="both"), :]

    # 地址長度縮短
    data["Address"] = data["Address"].str.slice(stop=30)
    data = data.loc[~data["Address"].isna(), :]

    # 6. 管理 / 隔間 / 備註 flag
    data.loc[data["Partition_YN"] == "有", "DRPD_Partition"] = "Y"
    data.loc[data["DRPD_Partition"] != "Y", "DRPD_Partition"] = "N"

    data.loc[data["Management_YN"] == "有", "DRPD_Management"] = "Y"
    data.loc[data["DRPD_Management"] != "Y", "DRPD_Management"] = "N"

    data.loc[data["Note"].isna(), "DRPD_HasNote"] = "N"
    data.loc[data["DRPD_HasNote"] != "N", "DRPD_HasNote"] = "Y"

    # 7. 建物年齡
    comp_date = pd.to_datetime(data["Completion_Date"], errors="coerce")
    data["DRPD_BuildingAge"] = data["Trading_Date"].dt.year - comp_date.dt.year
    data.loc[data["DRPD_BuildingAge"] < 0, "DRPD_BuildingAge"] = 0
    data["DRPD_BuildingAge"] = data["DRPD_BuildingAge"].fillna(10000)

    # 8. 面積 / 價格單位換算
    for col in ["Land_Trans_Area", "Trans_Area", "Total_Price", "Unit_Price"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data["Land_Trans_Area"] = (data["Land_Trans_Area"] * 0.3025).round(2)
    data["Trans_Area"] = (data["Trans_Area"] * 0.3025).round(2)
    data["Total_Price"] = (data["Total_Price"] / 10000).round(4)
    data["Unit_Price"] = (data["Unit_Price"] / (10000 * 0.3025)).round(4)
    data["Unit_Price"] = data["Unit_Price"].fillna(0)

    # 9. 座標處理
    data["DRPD_TargetX"] = pd.to_numeric(data["Trading_Target_X"], errors="coerce").round(4)
    data["DRPD_TargetY"] = pd.to_numeric(data["Trading_Target_Y"], errors="coerce").round(4)

    # 10. 建物型態 flag
    cond_main = ~data["Trading_Target"].isin(["土地", "車位"])

    cond_apt = data["Building_Type"].isin(["公寓(5樓含以下無電梯)"])
    cond_tower = data["Building_Type"].isin(["住宅大樓(11層含以上有電梯)", "華廈(10層含以下有電梯)"])
    cond_town = data["Building_Type"].isin(["透天厝"])

    data.loc[cond_main & cond_apt, "DRPD_BuildingTypeFlag"] = "01"
    data.loc[
        cond_main & cond_tower & (data["DRPD_BuildingTypeFlag"].isna()),
        "DRPD_BuildingTypeFlag",
    ] = "02"
    data.loc[
        cond_main & cond_town & (data["DRPD_BuildingTypeFlag"].isna()),
        "DRPD_BuildingTypeFlag",
    ] = "03"
    data["DRPD_BuildingTypeFlag"] = data["DRPD_BuildingTypeFlag"].fillna("04")

    # 11. 建物 Seg（年齡 x 型態）
    data["DRPD_BuildingSeg"] = "na"

    # 公寓
    mask = data["DRPD_BuildingTypeFlag"] == "01"
    data.loc[mask & data["DRPD_BuildingAge"].between(0, 10, inclusive="both"), "DRPD_BuildingSeg"] = "01"
    data.loc[mask & data["DRPD_BuildingAge"].between(11, 20, inclusive="both"), "DRPD_BuildingSeg"] = "03"
    data.loc[mask & data["DRPD_BuildingAge"].between(21, 999, inclusive="both"), "DRPD_BuildingSeg"] = "04"

    # 大樓/華廈
    mask = data["DRPD_BuildingTypeFlag"] == "02"
    data.loc[mask & data["DRPD_BuildingAge"].between(0, 10, inclusive="both"), "DRPD_BuildingSeg"] = "06"
    data.loc[mask & data["DRPD_BuildingAge"].between(11, 20, inclusive="both"), "DRPD_BuildingSeg"] = "08"
    data.loc[mask & data["DRPD_BuildingAge"].between(21, 999, inclusive="both"), "DRPD_BuildingSeg"] = "09"

    # 透天
    mask = data["DRPD_BuildingTypeFlag"] == "03"
    data.loc[mask & data["DRPD_BuildingAge"].between(0, 10, inclusive="both"), "DRPD_BuildingSeg"] = "16"
    data.loc[mask & data["DRPD_BuildingAge"].between(11, 20, inclusive="both"), "DRPD_BuildingSeg"] = "18"
    data.loc[mask & data["DRPD_BuildingAge"].between(21, 999, inclusive="both"), "DRPD_BuildingSeg"] = "19"

    data.loc[data["DRPD_BuildingSeg"] == "na", "DRPD_BuildingSeg"] = "99"

    # 12. 郵遞區號 merge
    zip_code = pd.read_excel(PATH_ZIP, dtype=str).rename(columns={"city": "City", "town": "District"})
    data = data.merge(zip_code, on=["City", "District"], how="left")

    # 13. 排序欄位、掛流水號
    data = data.reset_index().rename(columns={"index": "DRPD_Sequence"})
    data = data.rename(columns=DGISKEY)
    data = data[[c for c in DGISKEY_LIST if c in data.columns]]
    # 缺的欄位補空字串
    for col in DGISKEY_LIST:
        if col not in data.columns:
            data[col] = ""

    # 14. 算 FishID
    data = fishID_get(data, col_x="DRPD_TargetX", col_y="DRPD_TargetY")

    # 15. 基礎檢查 & 匯出
    if (data["DRPD_BuildingSeg"] == "na").any():
        print("Column DRPD_BuildingSeg is ERROR")
    elif (data["DRPD_BuildingTypeFlag"].isna()).any():
        print("Column DRPD_BuildingTypeFlag is ERROR")
    else:
        data.to_csv(join(path_wb, FILE_SEND), sep="|", index=False, encoding="utf8")
        picklesave(data, join(path_wb, "realestate_send"))

    # 16. 加工回來檔案簡單檢查（workbench/processing）
    data_complete = pd.read_csv(
        join(path_processing, FILE_TOTAL),
        dtype=str,
        delimiter="|",
        encoding="utf8",
    )
    # 去掉 TradeDate 時分秒
    data_complete["DRPD_TradeDate"] = data_complete["DRPD_TradeDate"].str.split(" ", expand=True)[0]
    data_complete.to_csv(
        join(path_processing, FILE_TOTAL),
        sep="|",
        index=False,
        encoding="utf8",
    )

    # 簡單檢查幾個欄位值域
    print("DRPD_EParkingPrice unique:", data_complete["DRPD_EParkingPrice"].unique())
    print("DRPD_ModifyFlag unique:", data_complete["DRPD_ModifyFlag"].unique())
    print("DRPD_SpecialTradeFlag unique:", data_complete["DRPD_SpecialTradeFlag"].unique())


if __name__ == "__main__":
    main()
