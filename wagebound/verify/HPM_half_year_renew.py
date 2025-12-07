# -*- coding: utf-8 -*-
"""
DGIS 實價登錄清理主程式
Created on Thu Oct 19 16:56:27 2023
@author: Z00051711
"""

from wagebound.config.config import cityname, colname, dropcol, dgiskey_lis, dgiskey
from StevenTricks.io.file_utils import PathWalk_df, picklesave
from ctbc_project.StevenTricks.snt import strtodate

from copy import deepcopy
from os import makedirs
from os.path import join

import pandas as pd


# =============================================================================
# 日期區間與路徑設定
# =============================================================================

# 要 + 一個月，所以 periods 設 38
d = pd.date_range(start="2021-4", periods=38, freq="MS")
d_start = d.min()
d_end = d.max()
d_end_str = d_end.strftime("%Y-%m-%d")

# 最近 3 個月起算日（建物明細匯出用）
date_3m = (d_end - pd.DateOffset(months=3)).strftime("%Y-%m-%d")

raw_dir = fr"D:\DGIS\原始資料\{d_end.strftime('%Y%m')}"
wb_dir = fr"D:\DGIS\workbench\{d_end.strftime('%Y%m')}"
wb_processing_dir = join(wb_dir, "processing")

for p in (raw_dir, wb_dir, wb_processing_dir):
    makedirs(p, exist_ok=True)

FILE_TOTAL = "GEOM_CTBC_RealPriceDetail.csv"
FILE_BD = "building_{}_{}_v.xlsx".format(
    d[33].strftime("%Y%m")[2:],  # 起始年月（舊規則）
    d_end_str.replace("-", "")[2:6],  # 結束年月（YYMM）
)
FILE_XY = "GEOM_CTBC_RealPriceDetail_XY.csv"
FILE_SEND = "GEOM_CTBC_RealPriceDetail_send.csv"
FILE_FISHID_XLSX = "GEOM_CTBC_RealPriceDetail_fishid.xlsx"

ZIP_PATH = r"D:\Users\z00188600\AppData\Local\anaconda3\Lib\site-packages\ctbc_project\ZIP.xlsx"


# =============================================================================
# 讀取原始 Excel，依縣市／檔別整併
# =============================================================================

excel_paths = PathWalk_df(raw_dir, fileinclude=[".xls"], level=0)
excel_paths = excel_paths.loc[excel_paths["level"] == 0]

# 暫存各檔別的 DataFrame list，最後再 concat 一次
res = {}

for file_path in excel_paths["path"]:
    file_dict = pd.read_excel(file_path, sheet_name=None)

    # 判斷目前檔案對應哪個縣市
    city = None
    for vol, city_name in cityname.items():
        if f"list_{vol.lower()}" in file_path:
            city = city_name
            break
    if city is None:
        # 找不到縣市代碼就跳過（避免後面 City 欄位爆掉）
        continue

    # 開始處理此 Excel 中各 sheet
    for sheet_name, df in file_dict.items():
        # sheet 名可能是「不動產買賣_50000」→ 只取前段
        newkey = sheet_name.split("_")[0]

        if newkey not in ["建物", "不動產買賣"]:
            continue

        # 1) 先 drop 通用多餘欄
        df = df.drop(columns=["Unnamed: 35", "Unnamed: 0"], errors="ignore")

        # 2) 欄位 rename
        if newkey in colname:
            df = df.rename(columns=colname[newkey])

        # 3) 依檔別再 drop 一些欄位
        if newkey in dropcol:
            df = df.drop(columns=dropcol[newkey], errors="ignore")

        if df.empty:
            continue

        # 4) 加上 City 欄位
        df.insert(0, "City", city)

        # 5) 建物檔：把「民國年月日」拆成年月日並轉成 3+2+2 的字串
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

        # 6) 收進暫存 dict
        res.setdefault(newkey, []).append(df)

# 將同類別的 DataFrame list 合併
for key in list(res.keys()):
    res[key] = pd.concat(res[key], ignore_index=True)

# =============================================================================
# 存原始不動產買賣，並建立最近三個月建物明細 Excel
# =============================================================================

picklesave(res["不動產買賣"], join(wb_dir, "realestate_original"))

# 注意：這裡假設 Trading_Date 已經是可比較的日期或一致格式字串
real_estate_3m = deepcopy(
    res["不動產買賣"].loc[
        res["不動產買賣"]["Trading_Date"] >= date_3m, :
    ]
)

building_3m = deepcopy(
    res["建物"].loc[
        res["建物"]["Number"].isin(real_estate_3m["Number"].tolist()),
        :,
    ]
)

with pd.ExcelWriter(join(wb_dir, FILE_BD), engine="xlsxwriter") as writer:
    building_3m.to_excel(writer, sheet_name="building", index=False)

# 主資料改用 data 變數後續處理
data = deepcopy(res["不動產買賣"])
del res, real_estate_3m, building_3m


# =============================================================================
# 日期欄位正規化 & 寫出原始 CSV / PKL（含日期）
# =============================================================================

data[["Trading_Date", "Completion_Date"]] = data[
    ["Trading_Date", "Completion_Date"]
].applymap(strtodate)

picklesave(data, join(wb_dir, "realestate_date"))
data.to_csv(join(wb_dir, FILE_TOTAL), sep="|", index=False, encoding="utf8")


# =============================================================================
# 主體篩選與欄位清理
# =============================================================================

# 排除土地與特定建物型態
data = data.loc[data["Trading_Target"] != "土地", :]
data = data.loc[~data["Building_Type"].isin(["工廠", "倉庫", "農舍"]), :]

# 必須要有完工年月
data = data.loc[~data["Completion_Date"].isna(), :]

# 交易日限制在 d_start ~ d_end 之間
data["Trading_Date"] = pd.to_datetime(data["Trading_Date"])
data = data.loc[data["Trading_Date"].between(d_start, d_end, inclusive="both"), :]

# 地址只留前 30 字
data["Address"] = data["Address"].str.slice(stop=30)
data = data.loc[~data["Address"].isna(), :]

# 格局隔間、管理組織 → Y/N
data.loc[data["Partition_YN"] == "有", "DRPD_Partition"] = "Y"
data.loc[data["DRPD_Partition"] != "Y", "DRPD_Partition"] = "N"

data.loc[data["Management_YN"] == "有", "DRPD_Management"] = "Y"
data.loc[data["DRPD_Management"] != "Y", "DRPD_Management"] = "N"

# 備註欄是否有資料 → HasNote
data.loc[data["Note"].isna(), "DRPD_HasNote"] = "N"
data.loc[data["DRPD_HasNote"] != "N", "DRPD_HasNote"] = "Y"

# 建物屋齡：交易年 - 完工年；負值視為 0，空值視為 10000
build_year = pd.to_datetime(
    data["Completion_Date"], errors="coerce", infer_datetime_format=True
).dt.year
trade_year = data["Trading_Date"].dt.year

data["DRPD_BuildingAge"] = trade_year - build_year
data.loc[data["DRPD_BuildingAge"] < 0, "DRPD_BuildingAge"] = 0
data["DRPD_BuildingAge"] = data["DRPD_BuildingAge"].fillna(10000)


# =============================================================================
# 單位換算（地坪 / 建坪 / 總價 / 單價）
# =============================================================================

data["Land_Trans_Area"] = (data["Land_Trans_Area"] * 0.3025).round(2)
data["Trans_Area"] = (data["Trans_Area"] * 0.3025).round(2)
data["Total_Price"] = (data["Total_Price"] / 10000).round(4)
data["Unit_Price"] = (data["Unit_Price"] / (10000 * 0.3025)).round(4)
data["Unit_Price"] = data["Unit_Price"].fillna(0)

# XY 座標取到小數點四位
data["DRPD_TargetX"] = data["Trading_Target_X"].round(4)
data["DRPD_TargetY"] = data["Trading_Target_Y"].round(4)


# =============================================================================
# 建物類型旗標（五樓公寓 / 大樓 / 透天 / 其他）
# =============================================================================

# 預設先給 na（如果前段沒有設過的話）
if "DRPD_BuildingTypeFlag" not in data.columns:
    data["DRPD_BuildingTypeFlag"] = "na"

mask_not_land_or_car = ~data["Trading_Target"].isin(["土地", "車位"])

mask_apartment = mask_not_land_or_car & data["Building_Type"].isin(
    ["公寓(5樓含以下無電梯)"]
)
mask_tower = mask_not_land_or_car & data["Building_Type"].isin(
    ["住宅大樓(11層含以上有電梯)", "華廈(10層含以下有電梯)"]
)
mask_townhouse = mask_not_land_or_car & data["Building_Type"].isin(["透天厝"])

data.loc[mask_apartment, "DRPD_BuildingTypeFlag"] = "01"
data.loc[mask_tower & (data["DRPD_BuildingTypeFlag"] == "na"), "DRPD_BuildingTypeFlag"] = "02"
data.loc[mask_townhouse & (data["DRPD_BuildingTypeFlag"] == "na"), "DRPD_BuildingTypeFlag"] = "03"
data.loc[data["DRPD_BuildingTypeFlag"] == "na", "DRPD_BuildingTypeFlag"] = "04"


# =============================================================================
# 建物分群（屋齡 × 類型）
# =============================================================================

if "DRPD_BuildingSeg" not in data.columns:
    data["DRPD_BuildingSeg"] = "na"

age = data["DRPD_BuildingAge"]

# 公寓
mask_btype_01 = data["DRPD_BuildingTypeFlag"] == "01"
data.loc[mask_btype_01 & age.between(0, 10, inclusive="both"), "DRPD_BuildingSeg"] = "01"
data.loc[
    mask_btype_01 & age.between(11, 20, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "03"
data.loc[
    mask_btype_01 & age.between(21, 999, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "04"

# 大樓
mask_btype_02 = data["DRPD_BuildingTypeFlag"] == "02"
data.loc[
    mask_btype_02 & age.between(0, 10, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "06"
data.loc[
    mask_btype_02 & age.between(11, 20, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "08"
data.loc[
    mask_btype_02 & age.between(21, 999, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "09"

# 透天
mask_btype_03 = data["DRPD_BuildingTypeFlag"] == "03"
data.loc[
    mask_btype_03 & age.between(0, 10, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "16"
data.loc[
    mask_btype_03 & age.between(11, 20, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "18"
data.loc[
    mask_btype_03 & age.between(21, 999, inclusive="both") & (data["DRPD_BuildingSeg"] == "na"),
    "DRPD_BuildingSeg",
] = "19"

# 其他類型統一成 99
data.loc[data["DRPD_BuildingSeg"] == "na", "DRPD_BuildingSeg"] = "99"


# =============================================================================
# 郵遞區號併入 & 欄位整理
# =============================================================================

zip_code = (
    pd.read_excel(ZIP_PATH, dtype=str)
    .rename(columns={"city": "City", "town": "District"})
)

data = pd.merge(data, zip_code, on=["City", "District"], how="left")

# 加上流水號
data = data.reset_index(drop=True).rename(columns={"index": "DRPD_Sequence"})

# 改欄位名稱為 DRPD_* 格式
data = data.rename(columns=dgiskey)

# 只保留 dgiskey_lis 指定欄位，多的都丟掉
data = data.drop(columns=[c for c in data.columns if c not in dgiskey_lis], errors="ignore")

# 若有缺欄位，補空字串
for col in dgiskey_lis:
    if col not in data.columns:
        data[col] = ""

# 匯出 XY，給本機 SAS 算 fishID
data[["DRPD_Number", "DRPD_TargetX", "DRPD_TargetY"]].to_csv(
    join(wb_dir, FILE_XY), sep="|", index=False, encoding="utf8"
)

# =============================================================================
# 讀取本機 SAS 算好的 fishID，回併
# =============================================================================

fishid = pd.read_excel(join(wb_dir, FILE_FISHID_XLSX), dtype=str)
data = pd.merge(
    data,
    fishid[["DRPD_Number", "DRPD_FishId"]],
    on="DRPD_Number",
    how="left",
)

# =============================================================================
# 最終送出檢查 & 匯出
# =============================================================================

if (data["DRPD_BuildingSeg"] == "na").any():
    print("Column DRPD_BuildingSeg is ERROR")
elif (data["DRPD_BuildingTypeFlag"] == "na").any():
    print("Column DRPD_BuildingTypeFlag is ERROR")
elif len(data.columns) != 36:
    print("Column length is ERROR")
else:
    data.to_csv(join(wb_dir, FILE_SEND), sep="|", index=False, encoding="utf8")
    picklesave(data, join(wb_dir, "realestate_send"))

# =============================================================================
# 加工回來後，再次檢查（由外部系統處理後）
# =============================================================================

data_complete = pd.read_csv(
    join(wb_processing_dir, FILE_TOTAL),
    dtype=str,
    delimiter="|",
    encoding="utf8",
)

# 下列三行通常在互動模式下看結果（Spyder / console）
data_complete["DRPD_EParkingPrice"].unique()      # 不能有 N、Y 以外值
data_complete["DRPD_ModifyFlag"].unique()         # 只能有 N、Y
data_complete["DRPD_SpecialTradeFlag"].unique()   # 只能有 N、Y
