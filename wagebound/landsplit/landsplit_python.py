# -*- coding: utf-8 -*-
"""
建築成本 × 房地分離：建物單價估算與 Var/Var2 校正流程

原始版：2025-11-05
整理優化版：2025-12-07
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

from wagebound.config.config_buildcost import (
    MIN_GROUP_COUNT,
    SPECIAL_REGIONS,
    START_DATE_STR,
    AP_WINDOW_MONTHS,
    CTBC_MONTHS,
    VAR_STEP,
    VAR2_STEP,
    SPECIAL_MIN_PRICE,
    GENERAL_MIN_PRICE,
    PATH_VARTABLE,
    PATH_BUILDINDEX,
    PATH_AP,
    PATH_LANDSPLIT,
    GROUP_LEVELS,
)

# ----------------------------------------------------------------------
# 小工具函式區
# ----------------------------------------------------------------------


def get_build_cost_seg(city: str, price_mean: float) -> str | None:
    """根據城市與單價平均（萬元），找對應建築成本 seg 標籤。"""
    city_cfg = build_cost.get(city, {})
    for seg_label, price_range in city_cfg.items():
        if price_mean in price_range:
            return seg_label
    return None


def assign_floor_flag(total_floor: int, material_temp: int) -> str | float:
    """
    依主建材 temp 與樓層數，給樓高分群標籤。
    temp:
        1: 鋼骨或 SRC
        2: RC / 鋼筋混凝土
        其他: 不細分樓高
    """
    if pd.isna(total_floor):
        return np.nan

    f = int(total_floor)

    if material_temp == 1:  # 鋼骨 / SRC
        if f <= 3:
            return "01.<=3"
        elif f <= 5:
            return "02.<=5"
        elif f <= 8:
            return "03.<=8"
        elif f <= 10:
            return "04.<=10"
        else:
            return "05.>10"

    if material_temp == 2:  # RC
        if f <= 3:
            return "01.<=3"
        elif f <= 5:
            return "02.<=5"
        else:
            return "03.>5"

    return np.nan


def categorize_building_age2(age: int) -> str:
    """建物屋齡粗分區間標籤，給 Building_Age_flag2 用。"""
    bins = [0, 10, 20, 30, np.inf]
    labels = ["01.<=10", "02.10< & <=20", "03.20< & <=30", "08.>30"]
    return pd.cut([age], bins=bins, labels=labels, right=True, include_lowest=True)[0]


def determine_seg_final(city: str, zip_code: str, floor_flag: str,
                        seg_map_zip, seg_map_floor, seg_map_city) -> str | float:
    """依照 zip → floor → city 的優先順序決定 seg_final。"""
    key_zip = (city, zip_code)
    if key_zip in seg_map_zip:
        return seg_map_zip[key_zip]

    key_floor = (city, floor_flag)
    if key_floor in seg_map_floor:
        return seg_map_floor[key_floor]

    return seg_map_city.get(city, np.nan)


def lookup_seg_price(data_buildcost: pd.DataFrame,
                     city: str,
                     floor_flag: str,
                     material_temp: int,
                     seg_label: str) -> float | None:
    """從建築成本表查詢 seg 單價（回傳萬元）。"""
    mask = (
        (data_buildcost["city"] == city)
        & (data_buildcost["total_floor_flag"] == floor_flag)
        & (data_buildcost["Main_Material_Code"] == material_temp)
    )
    rec = data_buildcost.loc[mask]
    if rec.empty or seg_label not in rec.columns:
        return None
    price = rec.iloc[0][seg_label]  # 元
    if pd.isna(price):
        return None
    return price / 10000.0  # 萬元


def round_to_step(x: float, step: float) -> float:
    """將數值四捨五入到指定刻度，例如 step=0.2."""
    if pd.isna(x):
        return x
    return round(step * round(x / step), 1)


# ----------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------


def main():
    today_str = date.today().strftime("%Y%m%d")

    # ---- 1. 讀取資料 ----

    # 策略系統變數表（多 sheet）
    data_var = pd.read_excel(PATH_VARTABLE, sheet_name=None)

    # 建築工程總指數
    data_buildindex = pd.read_excel(PATH_BUILDINDEX, sheet_name="月")
    # 統計期 → apply_date（月初）
    data_buildindex["apply_date"] = (
        data_buildindex["統計期"]
        .astype(str)
        .str.replace("年", "-")
        .str.replace("月", "-")
        .str.replace("日", "", regex=False)
    )
    data_buildindex["apply_date"] = pd.to_datetime(
        data_buildindex["apply_date"], format="%Y-%m-%d", errors="coerce"
    ).dt.to_period("M").dt.to_timestamp()

    # 建築成本表相關 view
    data_buildcost = data_var["build_cost_table"].drop_duplicates(
        subset=["city", "total_floor_flag", "Main_Material_Code"]
    )
    data_buildcost_upload = (
        data_var["build_cost_table"]
        .drop_duplicates()
        .rename(columns={"city": "After_five", "zip_code": "Area_Nbr"})
        .astype(str)
    )
    data_buildcost_zip = data_var["build_cost_table"].drop_duplicates(
        subset=["zip_code", "Main_Material_Code", "total_floor_flag"]
    )
    data_buildcost_city = data_var["build_cost_table"].drop_duplicates(
        subset=["city", "Main_Material_Code", "total_floor_flag"]
    )
    data_remaining_durable = data_var["remaining_durable_table"].rename(
        columns={"Main_Material_Code": "Main_Material_Code_ref"}
    )

    # DGIS 成交明細
    data_ap = pd.read_csv(
        PATH_AP,
        sep="|",
        parse_dates=["DRPD_TradeDate", "DRPD_CompletionDate"],
        dtype={"DRPD_ZipCode": str},
        low_memory=False,
    )

    # CTBC 內部資料
    data_ctbc = pd.read_excel(join(PATH_LANDSPLIT, "ctbc_inside.xlsx"))

    # ---- 2. 主建材 & 樓層 flag ----

    # AP：主建材暫存代碼
    data_ap["Main_Material_Code_temp"] = np.nan

    material_patterns = [
        (r"鋼骨|SRC|S．R．C", 1),
        (r"鋼筋混凝土|RC|R．C", 2),
        (r"加強磚", 3),
        (r"鋼架", 4),
    ]

    for pattern, code in material_patterns:
        mask = data_ap["DRPD_MainMaterial"].str.contains(pattern, na=False)
        mask &= data_ap["Main_Material_Code_temp"].isna()
        data_ap.loc[mask, "Main_Material_Code_temp"] = code

    # 其他統一歸類為 5
    data_ap["Main_Material_Code_temp"].fillna(5, inplace=True)

    # CTBC：主建材代碼轉換
    data_ctbc["Main_Material_Code_ref"] = data_ctbc["Main_Material_Code"].map(
        lambda x: ctbc_mainmaterial_ref.get(x, x)
    )
    data_ctbc["Main_Material_Code_temp"] = data_ctbc["Main_Material_Code_ref"].map(
        lambda x: ctbc_mainmaterial_ref_temp.get(x, 2)
    )

    # 樓層區間 flag
    data_ap["total_floor_flag"] = data_ap.apply(
        lambda r: assign_floor_flag(r["DRPD_TotalFloorFlag"], r["Main_Material_Code_temp"]),
        axis=1,
    )
    data_ctbc["total_floor_flag"] = data_ctbc.apply(
        lambda r: assign_floor_flag(r["Total_Floor_Cnt"], r["Main_Material_Code_temp"]),
        axis=1,
    )

    # ---- 3. 資料過濾 ----

    # AP：排除用途 / 備註 / 非合理樓層
    mask_purpose_valid = (
        data_ap["DRPD_MainPurpose"].notna()
        & ~data_ap["DRPD_MainPurpose"].isin(["工業用", "其他", "農業用"])
    )
    mask_no_note = data_ap["DRPD_NoteFlag"].isna()
    mask_floor_range = data_ap["DRPD_TransFloorFlag"].between(2, 998)

    data_ap = data_ap[mask_purpose_valid & mask_no_note & mask_floor_range].copy()

    # CTBC：標準化城市名稱，限定建材＆樓層
    data_ctbc.replace(cityname_change, inplace=True, regex=True)
    data_ctbc = data_ctbc[
        data_ctbc["Main_Material_Code"].isin([1, 2, 3, 4])
        & (data_ctbc["total_floor_flag"] != "05.>10")
    ].copy()

    # ---- 4. 建立時間窗 ----

    start_date = pd.to_datetime(START_DATE_STR)
    end_date_ap = start_date + pd.DateOffset(months=AP_WINDOW_MONTHS)

    # AP：近 N 月
    data_ap = data_ap[
        data_ap["DRPD_TradeDate"].between(start_date, end_date_ap, inclusive="left")
    ].copy()

    # CTBC：依 Application_Nbr 前 6 碼（年月）篩 N 個月
    ctbc_months = pd.date_range(
        start=start_date, periods=CTBC_MONTHS, freq="MS"
    ).strftime("%Y%m")
    data_ctbc = data_ctbc[
        data_ctbc["Application_Nbr"].str.slice(0, 6).isin(ctbc_months)
    ].copy()

    # 建物屋齡分段欄位（如果原始檔沒有，就自己建一個）
    if "Building_Age_flag2" not in data_ctbc.columns:
        data_ctbc["Building_Age_flag2"] = data_ctbc["Building_Age"].apply(
            lambda x: categorize_building_age2(x) if pd.notna(x) else np.nan
        )

    # ------------------------------------------------------------------
    # 5. 市場成交價統計 → seg_final
    # ------------------------------------------------------------------

    # 不同層級的單價中位數
    pivot_zip = (
        data_ap.groupby(["DRPD_City", "DRPD_ZipCode"])["DRPD_UnitPriceRevised"]
        .agg(median_price="median", count="size")
        .reset_index()
    )
    pivot_floor = (
        data_ap.groupby(["DRPD_City", "total_floor_flag"])["DRPD_UnitPriceRevised"]
        .agg(median_price="median", count="size")
        .reset_index()
    )
    pivot_city = (
        data_ap.groupby("DRPD_City")["DRPD_UnitPriceRevised"]
        .agg(median_price="median", count="size")
        .reset_index()
    )

    # 样本數門檻
    pivot_zip = pivot_zip[pivot_zip["count"] > MIN_GROUP_COUNT].copy()
    pivot_floor = pivot_floor[pivot_floor["count"] > MIN_GROUP_COUNT].copy()
    # city 不設門檻

    # 中位數 → seg
    pivot_zip["seg_final"] = pivot_zip.apply(
        lambda r: get_build_cost_seg(r["DRPD_City"], round(r["median_price"])), axis=1
    )
    pivot_floor["seg_final"] = pivot_floor.apply(
        lambda r: get_build_cost_seg(r["DRPD_City"], round(r["median_price"])), axis=1
    )
    pivot_city["seg_final"] = pivot_city.apply(
        lambda r: get_build_cost_seg(r["DRPD_City"], round(r["median_price"])), axis=1
    )

    # 映射 dict
    seg_map_zip = pivot_zip.set_index(["DRPD_City", "DRPD_ZipCode"])["seg_final"].to_dict()
    seg_map_floor = pivot_floor.set_index(["DRPD_City", "total_floor_flag"])["seg_final"].to_dict()
    seg_map_city = pivot_city.set_index("DRPD_City")["seg_final"].to_dict()

    # CTBC 每筆案件 seg_final
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

    # 建築成本表上傳用：掛上 seg_final（zip / floor / city）
    upload_zip = pivot_zip[["DRPD_City", "DRPD_ZipCode", "seg_final"]].rename(
        columns={"DRPD_City": "After_five", "DRPD_ZipCode": "Area_Nbr"}
    )
    upload_floor = pivot_floor[["DRPD_City", "total_floor_flag", "seg_final"]].rename(
        columns={"DRPD_City": "After_five", "seg_final": "seg_final_floor"}
    )
    upload_city = pivot_city[["DRPD_City", "seg_final"]].rename(
        columns={"DRPD_City": "After_five", "seg_final": "seg_final_city"}
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

    # seg_final 優先順序：zip → floor → city
    data_buildcost_upload["seg_final"] = data_buildcost_upload["seg_final"].fillna(
        data_buildcost_upload["seg_final_floor"]
    )
    data_buildcost_upload["seg_final"] = data_buildcost_upload["seg_final"].fillna(
        data_buildcost_upload["seg_final_city"]
    )

    # Build_Cost_Key & Index
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

    # ------------------------------------------------------------------
    # 6. seg 單價 × 建築指數 × 耐久度 → final_price
    # ------------------------------------------------------------------

    # seg 單價（萬元）
    data_ctbc["seg_price_wan"] = data_ctbc.apply(
        lambda r: lookup_seg_price(
            data_buildcost,
            r["After_five"],
            r["total_floor_flag"],
            r["Main_Material_Code_temp"],
            r["seg_final"],
        ),
        axis=1,
    )

    # 建築工程總指數，依 Aprl_Date 所在月份 match
    data_ctbc["Aprl_Month"] = (
        pd.to_datetime(data_ctbc["Aprl_Date"], errors="coerce")
        .dt.to_period("M")
        .dt.to_timestamp()
    )
    data_ctbc = data_ctbc.merge(
        data_buildindex[["apply_date", "buildindex"]],
        left_on="Aprl_Month",
        right_on="apply_date",
        how="left",
    )
    data_ctbc["build_index_factor"] = data_ctbc["buildindex"] / 100.0

    # 耐久度表：durable_year、remaining_rate
    data_ctbc = data_ctbc.merge(
        data_remaining_durable[["Main_Material_Code_ref", "remaining_rate", "durable_year"]],
        on="Main_Material_Code_ref",
        how="left",
    )
    data_ctbc["remaining_year"] = data_ctbc["durable_year"] - data_ctbc["Building_Age"]

    # 調整建物單價（未加 Var/Var2）
    data_ctbc["seg_price_adj"] = data_ctbc["seg_price_wan"] * data_ctbc["build_index_factor"]

    # 四號公報：耐用年限內直線折舊；超過耐用年限取殘值
    within_life = data_ctbc["remaining_year"] > 0

    data_ctbc["final_price"] = np.where(
        within_life,
        data_ctbc["seg_price_adj"]
        * (
            1
            - (data_ctbc["Building_Age"] / data_ctbc["durable_year"])
            * (1 - data_ctbc["remaining_rate"])
        ),
        data_ctbc["seg_price_adj"] * data_ctbc["remaining_rate"],
    )

    # ------------------------------------------------------------------
    # 7. 分層 Var / Var2：實際單價 vs 模型單價 的校正
    # ------------------------------------------------------------------

    var_results = {}
    for level, keys in GROUP_LEVELS.items():
        agg = (
            data_ctbc.groupby(keys)
            .agg(
                median_buildprice=("BuildPrice", "median"),
                median_modelprice=("final_price", "median"),
                count=("Application_Nbr", "size"),
            )
            .reset_index()
        )

        # 細層級才套樣本數門檻
        if level in {"level1", "level2", "level3"}:
            agg = agg[agg["count"] > MIN_GROUP_COUNT].copy()

        # 避免除以 0
        agg = agg[agg["median_modelprice"] != 0]

        agg["Var"] = agg["median_buildprice"] / agg["median_modelprice"]
        agg["Var2"] = agg["median_buildprice"] - agg["median_modelprice"]
        var_results[level] = agg

    # 合併回主資料，依層級由細到粗填補 Var / Var2
    data_ctbc["Var"] = np.nan
    data_ctbc["Var2"] = np.nan
    data_ctbc["Var_level"] = np.nan

    for level, keys in GROUP_LEVELS.items():
        suffix_V = f"_{level}"
        tmp = var_results[level][keys + ["Var", "Var2"]].rename(
            columns={"Var": f"Var{suffix_V}", "Var2": f"Var2{suffix_V}"}
        )

        data_ctbc = data_ctbc.merge(tmp, on=keys, how="left")

        mask_fill = data_ctbc["Var"].isna() & data_ctbc[f"Var{suffix_V}"].notna()
        data_ctbc.loc[mask_fill, "Var"] = data_ctbc.loc[mask_fill, f"Var{suffix_V}"]
        data_ctbc.loc[mask_fill, "Var2"] = data_ctbc.loc[mask_fill, f"Var2{suffix_V}"]
        data_ctbc.loc[mask_fill, "Var_level"] = level

    # 仍缺值：不做調整
    data_ctbc["Var"].fillna(1.0, inplace=True)
    data_ctbc["Var2"].fillna(0.0, inplace=True)

    # 離散化 Var / Var2
    data_ctbc["Var"] = data_ctbc["Var"].astype(float).map(lambda x: round_to_step(x, VAR_STEP))
    data_ctbc["Var2"] = data_ctbc["Var2"].astype(float).map(lambda x: round_to_step(x, VAR2_STEP))

    # ------------------------------------------------------------------
    # 8. final_price_adj / final_price_adj2 & 地區地板
    # ------------------------------------------------------------------

    # 倍數調整
    data_ctbc["final_price_adj"] = np.where(
        data_ctbc["remaining_year"] > 0,
        data_ctbc["final_price"] * data_ctbc["Var"],
        data_ctbc["final_price"],
    )

    # 金額平移
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
        mask_special
        & (cond_new | cond_just_expired)
        & (data_ctbc["final_price_adj2"] < SPECIAL_MIN_PRICE["new"]),
        "final_price_adj2",
    ] = SPECIAL_MIN_PRICE["new"]

    data_ctbc.loc[
        mask_special
        & cond_mid_expired
        & (data_ctbc["final_price_adj2"] < SPECIAL_MIN_PRICE["mid"]),
        "final_price_adj2",
    ] = SPECIAL_MIN_PRICE["mid"]

    data_ctbc.loc[
        mask_special
        & cond_long_expired
        & (data_ctbc["final_price_adj2"] < SPECIAL_MIN_PRICE["long"]),
        "final_price_adj2",
    ] = SPECIAL_MIN_PRICE["long"]

    # 一般區域
    data_ctbc.loc[
        mask_general
        & (cond_new | cond_just_expired)
        & (data_ctbc["final_price_adj2"] < GENERAL_MIN_PRICE["new"]),
        "final_price_adj2",
    ] = GENERAL_MIN_PRICE["new"]

    data_ctbc.loc[
        mask_general
        & cond_mid_expired
        & (data_ctbc["final_price_adj2"] < GENERAL_MIN_PRICE["mid"]),
        "final_price_adj2",
    ] = GENERAL_MIN_PRICE["mid"]

    data_ctbc.loc[
        mask_general
        & cond_long_expired
        & (data_ctbc["final_price_adj2"] < GENERAL_MIN_PRICE["long"]),
        "final_price_adj2",
    ] = GENERAL_MIN_PRICE["long"]

    # ------------------------------------------------------------------
    # 9. 誤差檢查 & 輸出
    # ------------------------------------------------------------------

    data_ctbc["diff_final"] = data_ctbc["final_price"] - data_ctbc["BuildPrice"]
    data_ctbc["diff_adj"] = data_ctbc["final_price_adj"] - data_ctbc["BuildPrice"]
    data_ctbc["diff_adj2"] = data_ctbc["final_price_adj2"] - data_ctbc["BuildPrice"]

    data_ctbc["MAPE_final"] = (data_ctbc["diff_final"] / data_ctbc["BuildPrice"]).abs()
    data_ctbc["MAPE_adj"] = (data_ctbc["diff_adj"] / data_ctbc["BuildPrice"]).abs()
    data_ctbc["MAPE_adj2"] = (data_ctbc["diff_adj2"] / data_ctbc["BuildPrice"]).abs()

    # 多餘的 Var_xxx 欄位清掉（只保留 Var / Var2 / Var_level）
    for level in GROUP_LEVELS.keys():
        suffix = f"_{level}"
        drop_cols = [c for c in data_ctbc.columns if c.endswith(suffix)]
        data_ctbc.drop(columns=drop_cols, inplace=True, errors="ignore")

    # 輸出
    out_path = join(PATH_LANDSPLIT, f"Build_Cost_Table_{today_str}.xlsx")
    with pd.ExcelWriter(out_path) as writer:
        data_buildcost_upload.to_excel(writer, sheet_name="upload", index=False)
        data_ctbc.to_excel(writer, sheet_name="result_detail", index=False)


if __name__ == "__main__":
    main()
