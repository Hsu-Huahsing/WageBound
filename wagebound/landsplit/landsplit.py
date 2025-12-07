# -*- coding: utf-8 -*-
"""
建築成本 × 透天房地分離：建物單價估算與 Var/Var2 校正

final_price      : 依四號公報折舊，未調整
final_price_adj  : final_price 乘上 Var（倍數調整）
final_price_adj2 : final_price 加上 Var2（金額平移）

使用前提：
    - 先在 VDI 跑「透天房地分離」，輸出 ctbc_inside.xlsx
    - 本程式讀取：
        - 策略系統參數表（build_cost_table, remaining_durable_table）
        - 建築工程總指數
        - DGIS 成交明細
        - ctbc_inside.xlsx
"""

from datetime import date
from os.path import join

import numpy as np
import pandas as pd

from wagebound.config.config import (
    build_cost,
    ctbc_mainmaterial_ref,
    ctbc_mainmaterial_ref_temp,
    cityname_change,
    seg_price_num,
)

# ----------------------------------------------------------------------
# 參數設定
# ----------------------------------------------------------------------

TODAY_STR = date.today().strftime("%Y%m%d")

# 分組統計最低樣本數門檻
MIN_GROUP_COUNT = 30

# 特殊區域（平移調整的最低地板價不同）
SPECIAL_REGIONS = {"台中市", "南投縣", "彰化縣"}

# Var / Var2 離散化刻度
VAR_STEP = 0.2
VAR2_STEP = 0.5

# 建模起始日期（含），往後取 6 個月成交＋6 個月申貸資料
START_DATE_STR = "2025-04-01"

# 檔案路徑
PATH_VARTABLE = r"E:\數位專案\HPM2.0\2025-11RC\策略系統參數表彙整_20250528.xlsx"
PATH_BUILDINDEX = r"E:\數位專案\HPM2.0\2025-11RC\建築工程總指數251030.xlsx"
PATH_AP = r"D:\DGIS\workbench\202510\上傳DGIS\GEOM_CTBC_RealPriceDetail.csv"
PATH_LANDSPLIT = r"E:\數位專案\HPM2.0\2025-11RC"


# ----------------------------------------------------------------------
# 小工具函式
# ----------------------------------------------------------------------


def parse_roc_month(series: pd.Series) -> pd.Series:
    """
    將「民國年月日字串」轉為該月第一天的 Timestamp。
    例："113年9月30日" → 2024-09-01
    """
    df = series.astype(str).str.split("年|月|日", expand=True)
    df = df.rename(columns={0: "year", 1: "month", 2: "day"})
    df["day"] = "1"
    df["year"] = pd.to_numeric(df["year"], errors="coerce").add(1911).astype("Int64")
    return pd.to_datetime(df[["year", "month", "day"]], errors="coerce")


def get_build_cost_seg(city: str, price_mean: float) -> str | None:
    """
    根據城市與單價平均（整數）在 build_cost 裡找到 seg 標籤。
    build_cost 結構：{ city: { seg_label: range(...) } }
    """
    city_cfg = build_cost.get(city, {})
    for seg_label, price_range in city_cfg.items():
        if price_mean in price_range:
            return seg_label
    return None


def assign_floor_flag(total_floor, material_temp) -> str | float:
    """
    依主建材 temp 與樓層數，回傳樓高區間：
        temp=1: 鋼骨 / SRC
        temp=2: RC
        其他: 不細分，回傳 NaN
    """
    if pd.isna(total_floor):
        return np.nan
    f = int(total_floor)

    if material_temp == 1:
        if f <= 3:
            return "01.<=3"
        if f <= 5:
            return "02.<=5"
        if f <= 8:
            return "03.<=8"
        if f <= 10:
            return "04.<=10"
        return "05.>10"

    if material_temp == 2:
        if f <= 3:
            return "01.<=3"
        if f <= 5:
            return "02.<=5"
        return "03.>5"

    return np.nan


def categorize_building_age(age) -> str | float:
    """細分屋齡區間（Building_Age_flag）。"""
    if pd.isna(age):
        return np.nan
    bins = [0, 5, 10, 15, 20, 25, 30, 40, 50, np.inf]
    labels = [
        "01.<=5",
        "02.5< & <=10",
        "03.10< & <=15",
        "04.15< & <=20",
        "05.20< & <=25",
        "06.25< & <=30",
        "06.30< & <=40",
        "07.40< & <=50",
        "08.>50",
    ]
    return pd.cut([age], bins=bins, labels=labels, right=True, include_lowest=True)[0]


def categorize_building_age2(age) -> str | float:
    """粗分屋齡區間（Building_Age_flag2）。"""
    if pd.isna(age):
        return np.nan
    bins = [0, 10, 20, 30, np.inf]
    labels = ["01.<=10", "02.10< & <=20", "03.20< & <=30", "08.>30"]
    return pd.cut([age], bins=bins, labels=labels, right=True, include_lowest=True)[0]


def determine_seg_final(city, zip_code, floor_flag, seg_map_zip, seg_map_floor, seg_map_city):
    """seg_final 優先順序：zip → floor → city。"""
    key_zip = (city, zip_code)
    if key_zip in seg_map_zip:
        return seg_map_zip[key_zip]
    key_floor = (city, floor_flag)
    if key_floor in seg_map_floor:
        return seg_map_floor[key_floor]
    return seg_map_city.get(city, np.nan)


def lookup_seg_price_raw(
    data_buildcost: pd.DataFrame,
    city: str,
    floor_flag: str,
    material_temp: int,
    seg_label: str,
) -> float | None:
    """
    從 build_cost_table 查 seg 單價（「原始金額」，尚未除以 10000 或乘指數）。
    特例：main_material_temp=2 一律使用 seg1_price。
    """
    if pd.isna(seg_label):
        return None

    seg_col = "seg1_price" if material_temp == 2 else seg_label
    mask = (
        (data_buildcost["city"] == city)
        & (data_buildcost["total_floor_flag"] == floor_flag)
        & (data_buildcost["Main_Material_Code"] == material_temp)
    )
    rec = data_buildcost.loc[mask]

    if rec.empty or seg_col not in rec.columns:
        return None

    return rec.iloc[0][seg_col]


def round_to_step(x: float, step: float) -> float:
    """將數值四捨五入到指定刻度，例如 0.2、0.5。"""
    if pd.isna(x):
        return x
    return round(step * round(x / step), 1)


def label_diff_bucket(series: pd.Series) -> pd.Series:
    """
    將價差（final - BuildPrice）分群：
      (-inf,-4]   → 01.<=-4
      (-4,-2]     → 02.-4< & <=-2
      (-2,-1]     → 03.-2< & <=-1
      (-1,-0.5]   → 04.-1< & <=-0.5
      (-0.5,0]    → 05.-0.5< & <=0
      (0,0.5]     → 06.0< & <=0.5
      (0.5,1]     → 07.0.5< & <=1
      (1,2]       → 08.1< & <=2
      (2,4]       → 09.2< & <=4
      (4,inf)     → 10.>4
    """
    bins = [-np.inf, -4, -2, -1, -0.5, 0, 0.5, 1, 2, 4, np.inf]
    labels = [
        "01.<=-4",
        "02.-4< & <=-2",
        "03.-2< & <=-1",
        "04.-1< & <=-0.5",
        "05.-0.5< & <=0",
        "06.0< & <=0.5",
        "07.0.5< & <=1",
        "08.1< & <=2",
        "09.2< & <=4",
        "10.>4",
    ]
    return pd.cut(series, bins=bins, labels=labels, right=True, include_lowest=True)


# ----------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------


def main():
    # -------------------------
    # 1. 讀檔
    # -------------------------
    data_var = pd.read_excel(PATH_VARTABLE, sheet_name=None)

    data_buildindex = pd.read_excel(PATH_BUILDINDEX, sheet_name="月").rename(
        columns={"統計期": "apply_date", "建築工程總指數": "buildindex"}
    )
    data_buildindex["apply_date"] = parse_roc_month(data_buildindex["apply_date"])

    data_buildcost_upload = (
        data_var["build_cost_table"]
        .drop_duplicates()
        .rename(columns={"city": "After_five", "zip_code": "Area_Nbr"})
        .astype(str)
    )
    # build_cost_table 主表（不需要 price_level）
    data_buildcost = (
        data_var["build_cost_table"]
        .drop(columns=["zip_code", "price_level"])
        .drop_duplicates()
    )
    data_remaining_durable = data_var["remaining_durable_table"].rename(
        columns={"Main_Material_Code": "Main_Material_Code_ref"}
    )

    data_ap = pd.read_csv(
        PATH_AP,
        sep="|",
        parse_dates=["DRPD_TradeDate", "DRPD_CompletionDate"],
        low_memory=False,
        dtype={"DRPD_ZipCode": str},
    )

    data_ctbc = pd.read_excel(join(PATH_LANDSPLIT, "ctbc_inside.xlsx"))

    # -------------------------
    # 2. 主建材暫存代碼 / 樓高 flag / 屋齡 flag
    # -------------------------

    # DGIS 主建材暫存代碼
    data_ap["Main_Material_Code_temp"] = np.nan
    pattern_map = [
        (r"鋼骨|SRC|S．R．C", 1),
        (r"鋼筋混凝土|RC|R．C", 2),
        (r"加強磚", 3),
        (r"鋼架", 4),
    ]
    for pattern, code in pattern_map:
        mask = data_ap["DRPD_MainMaterial"].str.contains(pattern, regex=True, na=False)
        mask &= data_ap["Main_Material_Code_temp"].isna()
        data_ap.loc[mask, "Main_Material_Code_temp"] = code
    data_ap["Main_Material_Code_temp"].fillna(5, inplace=True)

    # CTBC 主建材轉碼
    data_ctbc["Main_Material_Code_ref"] = data_ctbc["Main_Material_Code"].map(
        lambda x: ctbc_mainmaterial_ref.get(x, x)
    )
    data_ctbc["Main_Material_Code_temp"] = data_ctbc["Main_Material_Code_ref"].map(
        lambda x: ctbc_mainmaterial_ref_temp.get(x, 2)
    )

    # 樓高 flag
    data_ap["total_floor_flag"] = data_ap.apply(
        lambda r: assign_floor_flag(r["DRPD_TotalFloorFlag"], r["Main_Material_Code_temp"]),
        axis=1,
    )
    data_ctbc["total_floor_flag"] = data_ctbc.apply(
        lambda r: assign_floor_flag(r["Total_Floor_Cnt"], r["Main_Material_Code_temp"]),
        axis=1,
    )

    # 用途 / 備註 / 樓層過濾
    mask_purpose = data_ap["DRPD_MainPurpose"].notna() & ~data_ap[
        "DRPD_MainPurpose"
    ].isin(["工業用", "其他", "農業用"])
    mask_note = data_ap["DRPD_NoteFlag"].isna()
    mask_floor = data_ap["DRPD_TransFloorFlag"].between(2, 998)
    data_ap = data_ap[mask_purpose & mask_note & mask_floor].copy()

    # 城市名稱標準化
    data_ctbc.replace(cityname_change, regex=True, inplace=True)

    # 屋齡 flag1 / flag2
    data_ctbc["Building_Age_flag"] = data_ctbc["Building_Age"].apply(
        categorize_building_age
    )
    data_ctbc["Building_Age_flag2"] = data_ctbc["Building_Age"].apply(
        categorize_building_age2
    )

    # 申請年月（Application_Nbr 前 6 碼）
    data_ctbc["Date"] = data_ctbc["Application_Nbr"].str.slice(0, 6)

    # 僅保留樓高不超過 10 且建材 1~4
    data_ctbc = data_ctbc[
        (data_ctbc["total_floor_flag"] != "05.>10")
        & data_ctbc["Main_Material_Code"].isin([1, 2, 3, 4])
    ].copy()

    # -------------------------
    # 3. 時間窗：近 6 個月成交 / 近 6 個月申貸
    # -------------------------
    start_date = pd.to_datetime(START_DATE_STR)
    date_range_ap = pd.date_range(
        start=start_date, periods=2, freq=pd.offsets.MonthBegin(6), inclusive="both"
    )
    date_range_ctbc = pd.date_range(
        start=start_date, periods=6, freq="MS"
    ).strftime("%Y%m")

    data_ap = data_ap[
        data_ap["DRPD_TradeDate"].between(date_range_ap[0], date_range_ap[1], inclusive="left")
    ].copy()
    data_ctbc = data_ctbc[data_ctbc["Date"].isin(date_range_ctbc)].copy()

    # -------------------------
    # 4. 成交價 → seg_final
    # -------------------------

    # ZIP level
    pivot_zip = (
        data_ap.groupby(["DRPD_City", "DRPD_ZipCode"])["DRPD_UnitPriceRevised"]
        .agg(median_price="median", count="size")
        .reset_index()
        .rename(columns={"DRPD_City": "After_five", "DRPD_ZipCode": "Area_Nbr"})
    )
    pivot_zip = pivot_zip[pivot_zip["count"] > MIN_GROUP_COUNT].copy()
    pivot_zip["seg_final"] = pivot_zip.apply(
        lambda r: get_build_cost_seg(r["After_five"], round(r["median_price"], 0)), axis=1
    )

    # floor level
    pivot_floor = (
        data_ap.groupby(["DRPD_City", "total_floor_flag"])["DRPD_UnitPriceRevised"]
        .agg(median_price="median", count="size")
        .reset_index()
        .rename(columns={"DRPD_City": "After_five"})
    )
    pivot_floor = pivot_floor[pivot_floor["count"] > MIN_GROUP_COUNT].copy()
    pivot_floor["seg_final"] = pivot_floor.apply(
        lambda r: get_build_cost_seg(r["After_five"], round(r["median_price"], 0)), axis=1
    )

    # city level（不設樣本數門檻）
    pivot_city = (
        data_ap.groupby("DRPD_City")["DRPD_UnitPriceRevised"]
        .agg(median_price="median", count="size")
        .reset_index()
        .rename(columns={"DRPD_City": "After_five"})
    )
    pivot_city["seg_final"] = pivot_city.apply(
        lambda r: get_build_cost_seg(r["After_five"], round(r["median_price"], 0)), axis=1
    )

    # seg 映射 dict
    seg_map_zip = pivot_zip.set_index(["After_five", "Area_Nbr"])["seg_final"].to_dict()
    seg_map_floor = pivot_floor.set_index(["After_five", "total_floor_flag"])["seg_final"].to_dict()
    seg_map_city = pivot_city.set_index("After_five")["seg_final"].to_dict()

    # CTBC 每筆 seg_final
    data_ctbc["Area_Nbr"] = data_ctbc["Area_Nbr"].astype(str)
    data_ctbc["seg_final"] = data_ctbc.apply(
        lambda r: determine_seg_final(
            r["After_five"],
            str(r["Area_Nbr"]),
            r["total_floor_flag"],
            seg_map_zip,
            seg_map_floor,
            seg_map_city,
        ),
        axis=1,
    )

    # build_cost_upload 補 seg_final（zip → floor → city）
    upload_zip = pivot_zip[["After_five", "Area_Nbr", "seg_final"]]
    upload_floor = pivot_floor[["After_five", "total_floor_flag", "seg_final"]].rename(
        columns={"seg_final": "seg_final_floor"}
    )
    upload_city = pivot_city[["After_five", "seg_final"]].rename(
        columns={"seg_final": "seg_final_city"}
    )

    data_buildcost_upload = data_buildcost_upload.merge(
        upload_zip, on=["After_five", "Area_Nbr"], how="left"
    )
    data_buildcost_upload = data_buildcost_upload.merge(
        upload_floor, on=["After_five", "total_floor_flag"], how="left"
    )
    data_buildcost_upload = data_buildcost_upload.merge(
        upload_city, on="After_five", how="left"
    )

    data_buildcost_upload["seg_final"] = data_buildcost_upload["seg_final"].fillna(
        data_buildcost_upload["seg_final_floor"]
    )
    data_buildcost_upload["seg_final"] = data_buildcost_upload["seg_final"].fillna(
        data_buildcost_upload["seg_final_city"]
    )

    # Build_Cost_Key / Index
    data_buildcost_upload["Build_Cost_Key"] = (
        data_buildcost_upload["Area_Nbr"]
        + "_"
        + data_buildcost_upload["total_floor_flag"].str[:2]
        + "_"
        + data_buildcost_upload["Main_Material_Code"].str.zfill(2)
    )
    data_buildcost_upload["Index"] = data_buildcost_upload["seg_final"].map(
        lambda x: seg_price_num.get(x, 1)
    )

    upload_cols = ["Build_Cost_Key"] + [f"segprice{i}" for i in range(1, 10)] + ["Index"]
    data_buildcost_upload = data_buildcost_upload.reindex(columns=upload_cols)

    # -------------------------
    # 5. seg 單價 × 建築指數 × 耐久度 → final_price
    # -------------------------

    # seg 原始金額（未除以 10000 / 未乘指數）
    data_ctbc["seg_price_raw"] = data_ctbc.apply(
        lambda r: lookup_seg_price_raw(
            data_buildcost,
            r["After_five"],
            r["total_floor_flag"],
            r["Main_Material_Code_temp"],
            r["seg_final"],
        ),
        axis=1,
    )

    # 主建材 3 / 4 加上 37,500（符合你舊程式的規則）
    mask_34 = data_ctbc["Main_Material_Code"].isin([3, 4])
    data_ctbc.loc[mask_34, "seg_price_raw"] = (
        data_ctbc.loc[mask_34, "seg_price_raw"].astype(float) + 37500
    )

    # Aprl_Date 對應建築工程總指數
    data_ctbc["Aprl_Month"] = pd.to_datetime(
        data_ctbc["Aprl_Date"], errors="coerce"
    ).dt.to_period("M").dt.to_timestamp()
    data_ctbc = data_ctbc.merge(
        data_buildindex[["apply_date", "buildindex"]],
        left_on="Aprl_Month",
        right_on="apply_date",
        how="left",
    )
    data_ctbc["buildindex"] = data_ctbc["buildindex"] / 100.0

    # 耐久度與殘值率
    data_ctbc = data_ctbc.merge(
        data_remaining_durable[["Main_Material_Code_ref", "remaining_rate", "durable_year"]],
        on="Main_Material_Code_ref",
        how="left",
    )
    data_ctbc["remaining_year"] = data_ctbc["durable_year"] - data_ctbc["Building_Age"]

    # seg 單價（萬元）× 建築指數
    data_ctbc["seg_price_wan"] = data_ctbc["seg_price_raw"].astype(float) / 10000.0
    data_ctbc["seg_price_adj"] = data_ctbc["seg_price_wan"] * data_ctbc["buildindex"]

    # 四號公報：耐用年限內直線折舊，超過耐用年限取殘值
    within_life = data_ctbc["remaining_year"] > 0

    data_ctbc["final_price"] = np.where(
        within_life,
        data_ctbc["seg_price_adj"]
        - (data_ctbc["Building_Age"] / data_ctbc["durable_year"])
        * (1 - data_ctbc["remaining_rate"])
        * data_ctbc["seg_price_adj"],
        data_ctbc["seg_price_adj"] * data_ctbc["remaining_rate"],
    )

    # -------------------------
    # 6. Var / Var2 分層校正
    # -------------------------

    group_levels = {
        "level1": ["Area_Nbr", "total_floor_flag", "Building_Age_flag2"],
        "level2": ["Area_Nbr", "Building_Age_flag2"],
        "level3": ["Area_Nbr"],
        "level4": ["County"],
    }

    var_results = {}
    for level, keys in group_levels.items():
        agg = (
            data_ctbc.groupby(keys)
            .agg(
                Application_Nbr=("Application_Nbr", "size"),
                BuildPrice=("BuildPrice", "median"),
                final_price=("final_price", "median"),
            )
            .reset_index()
        )

        if level in {"level1", "level2", "level3"}:
            agg = agg[agg["Application_Nbr"] > MIN_GROUP_COUNT].copy()

        agg = agg[agg["final_price"] != 0].copy()
        agg["Var"] = agg["BuildPrice"] / agg["final_price"]
        agg["Var2"] = agg["BuildPrice"] - agg["final_price"]
        var_results[level] = agg

    data_ctbc["Var"] = np.nan
    data_ctbc["Var2"] = np.nan
    data_ctbc["Var_level"] = np.nan

    for level, keys in group_levels.items():
        suffix = f"_{level}"
        tmp = var_results[level][keys + ["Var", "Var2"]].rename(
            columns={"Var": f"Var{suffix}", "Var2": f"Var2{suffix}"}
        )
        data_ctbc = data_ctbc.merge(tmp, on=keys, how="left")

        mask_fill = data_ctbc["Var"].isna() & data_ctbc[f"Var{suffix}"].notna()
        data_ctbc.loc[mask_fill, "Var"] = data_ctbc.loc[mask_fill, f"Var{suffix}"]
        data_ctbc.loc[mask_fill, "Var2"] = data_ctbc.loc[mask_fill, f"Var2{suffix}"]
        data_ctbc.loc[mask_fill, "Var_level"] = level

    # 缺值：不做調整
    data_ctbc["Var"].fillna(1.0, inplace=True)
    data_ctbc["Var2"].fillna(0.0, inplace=True)

    # 離散化
    data_ctbc["Var"] = data_ctbc["Var"].astype(float).map(lambda x: round_to_step(x, VAR_STEP))
    data_ctbc["Var2"] = data_ctbc["Var2"].astype(float).map(lambda x: round_to_step(x, VAR2_STEP))

    # 清掉中間 Var_xxx 欄位
    for level in group_levels.keys():
        suffix = f"_{level}"
        drop_cols = [c for c in data_ctbc.columns if c.endswith(suffix)]
        data_ctbc.drop(columns=drop_cols, inplace=True, errors="ignore")

    # -------------------------
    # 7. final_price_adj / final_price_adj2 ＋地板價
    # -------------------------

    data_ctbc["final_price_adj"] = np.where(
        data_ctbc["remaining_year"] > 0,
        data_ctbc["final_price"] * data_ctbc["Var"],
        data_ctbc["final_price"],
    )

    data_ctbc["final_price_adj2"] = np.where(
        data_ctbc["remaining_year"] > 0,
        data_ctbc["final_price"] + data_ctbc["Var2"],
        data_ctbc["final_price"],
    )

    mask_special = data_ctbc["After_five"].isin(SPECIAL_REGIONS)
    mask_general = ~mask_special

    cond_new = data_ctbc["remaining_year"] > 0
    cond_just_expired = data_ctbc["remaining_year"].between(-3, 0)
    cond_mid_expired = data_ctbc["remaining_year"].between(-9, -4)
    cond_long_expired = data_ctbc["remaining_year"] <= -10

    # 特殊區域
    data_ctbc.loc[
        mask_special & (cond_new | cond_just_expired) & (data_ctbc["final_price_adj2"] < 3),
        "final_price_adj2",
    ] = 3
    data_ctbc.loc[
        mask_special & cond_mid_expired & (data_ctbc["final_price_adj2"] < 2.5),
        "final_price_adj2",
    ] = 2.5
    data_ctbc.loc[
        mask_special & cond_long_expired & (data_ctbc["final_price_adj2"] < 1.5),
        "final_price_adj2",
    ] = 1.5

    # 一般區域
    data_ctbc.loc[
        mask_general & (cond_new | cond_just_expired) & (data_ctbc["final_price_adj2"] < 1),
        "final_price_adj2",
    ] = 1
    data_ctbc.loc[
        mask_general & cond_mid_expired & (data_ctbc["final_price_adj2"] < 0.8),
        "final_price_adj2",
    ] = 0.8
    data_ctbc.loc[
        mask_general & cond_long_expired & (data_ctbc["final_price_adj2"] < 0.5),
        "final_price_adj2",
    ] = 0.5

    # -------------------------
    # 8. 誤差 / MAPE / diff 分群
    # -------------------------

    data_ctbc["final_price_diff"] = data_ctbc["final_price"] - data_ctbc["BuildPrice"]
    data_ctbc["final_price_adj_diff"] = (
        data_ctbc["final_price_adj"] - data_ctbc["BuildPrice"]
    )
    data_ctbc["final_price_adj2_diff"] = (
        data_ctbc["final_price_adj2"] - data_ctbc["BuildPrice"]
    )

    data_ctbc["Build_MAPE"] = (
        data_ctbc["final_price_diff"] / data_ctbc["BuildPrice"]
    ).abs()
    data_ctbc["Build_MAPE_adj"] = (
        data_ctbc["final_price_adj_diff"] / data_ctbc["BuildPrice"]
    ).abs()
    data_ctbc["Build_MAPE_adj2"] = (
        data_ctbc["final_price_adj2_diff"] / data_ctbc["BuildPrice"]
    ).abs()

    # diff 分段旗標
    data_ctbc["diff_flag"] = label_diff_bucket(data_ctbc["final_price_diff"])
    data_ctbc["adj_diff_flag"] = label_diff_bucket(data_ctbc["final_price_adj_diff"])
    data_ctbc["adj2_diff_flag"] = label_diff_bucket(data_ctbc["final_price_adj2_diff"])

    # -------------------------
    # 9. 輸出
    # -------------------------
    out_path = join(PATH_LANDSPLIT, f"Build_Cost_Table_{TODAY_STR}.xlsx")
    with pd.ExcelWriter(out_path) as writer:
        # 上傳用建築成本表
        data_buildcost_upload.to_excel(writer, sheet_name="upload", index=False)
        # 模型細節與誤差檢查
        data_ctbc.to_excel(writer, sheet_name="result_detail", index=False)


if __name__ == "__main__":
    main()
