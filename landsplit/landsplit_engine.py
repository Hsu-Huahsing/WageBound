# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 10:25:12 2025

@author: Z00051711
"""

import pandas as pd
import numpy as np
from datetime import date
from os.path import join
from ctbc_project.config import build_cost, ctbc_mainmaterial_ref, ctbc_mainmaterial_ref_temp, cityname_change, seg_price_num


# 參數與配置
MIN_GROUP_COUNT = 30 # 分組統計的最低樣本數門檻
SPECIAL_REGIONS = {"台中市", "南投縣", "彰化縣"} # 特殊調整區域
today_str = date.today().strftime("%Y%m%d")

path_vartable_pcsm = r"D:\數位專案\透天房地分離\策略系統\Build_Cost_Table.csv"
path_vartable = r"E:\數位專案\HPM2.0\2025-11RC\策略系統參數表彙整_20250528.xlsx"
path_buildindex = r"E:\數位專案\HPM2.0\2025-11RC\建築工程總指數251030.xlsx"
path_ap = r'D:\DGIS\workbench\202510\上傳DGIS\GEOM_CTBC_RealPriceDetail.csv'
path_landsplit = r"E:\數位專案\HPM2.0\2025-11RC"

# ----1. 定義輔助對照表與函式----

# (假設從ctbc_project.config中匯入以下字典)
# build_cost: {city: {seg_level: range_set, ...}}
# ctbc_mainmaterial_ref, ctbc_mainmaterial_ref_temp: 主建材代碼對照字典
# seg_price_num: {"seg1_price":1, "seg2_price":2, ...}

def get_build_cost_seg(city: str, price_mean: float) -> str:
    """根據城市和價格均值，尋找所屬的建築成本區間(seg)標籤。"""
    for seg_label, price_range in build_cost.get(city, {}).items():
        if price_mean in price_range:
            return seg_label
    return None

def assign_floor_flag(total_floor: int, material_temp: int) -> str:
    """依主建材類別(temp)和樓層數，分配樓高區間標籤。"""
    if material_temp == 1: # 鋼骨或SRC結構
        if total_floor <= 3: return "01.<=3"
        elif total_floor <= 5: return "02.<=5"
        elif total_floor <= 8: return "03.<=8"
        elif total_floor <= 10: return "04.<=10"
        else: return "05.>10"
    elif material_temp == 2: # RC鋼筋混凝土或類似結構
        if total_floor <= 3: return "01.<=3"
        elif total_floor <= 5: return "02.<=5"
        else: return "03.>5"
    else:
        return np.nan # 其他結構不細分樓高

def categorize_building_age(age: int) -> str:
    """將建物屋齡依區間轉為類別標籤 (細分區間)。"""
    bins = [0,5,10,15,20,25,30,40,50, np.inf]
    labels = ["01.<=5", "02.5< & <=10", "03.10< & <=15", "04.15< & <=20",
        "05.20< & <=25", "06.25< & <=30", "06.30< & <=40",
        "07.40< & <=50", "08.>50"]
    # pd.cut將連續值分段標籤 [oai_citation:5‡pandas.pydata.org](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.cut.html#:~:text=Use%20cut%20when%20you%20need,specified%20array%20of%20bins)
    return pd.cut([age], bins=bins, labels=labels, right=True, include_lowest=True)[0]

def categorize_building_age2(age: int) -> str:
    """將建物屋齡依區間轉為類別標籤 (粗分區間)。"""
    bins = [0,10,20,30, np.inf]
    labels = ["01.<=10", "02.10< & <=20", "03.20< & <=30", "08.>30"]
    return pd.cut([age], bins=bins, labels=labels, right=True, include_lowest=True)[0]

# ----2. 資料讀取與預處理----

# 讀取各資料表
data_var_pcsm = pd.read_csv(path_vartable_pcsm, dtype=str)
data_var = pd.read_excel(path_vartable, sheet_name=None)
data_buildindex = pd.read_excel(path_buildindex, sheet_name="月")
data_buildindex["apply_date"] = pd.to_datetime(data_buildindex["統計期"].str.replace("年","-").str.replace("月","-").str.replace("日",""),format="%Y-%m-%d", errors="coerce").dt.to_period('M').dt.to_timestamp() # 民國年轉西元並取該月第一天

# 相關資料表整理
data_buildcost = data_var["build_cost_table"].drop_duplicates(subset=["city","total_floor_flag","Main_Material_Code"])
data_buildcost_upload = data_var["build_cost_table"].drop_duplicates().rename(columns={"city":"After_five","zip_code":"Area_Nbr"}).astype(str)
data_buildcost_zip = data_var["build_cost_table"].drop_duplicates(subset=["zip_code","Main_Material_Code","total_floor_flag"])
data_buildcost_city = data_var["build_cost_table"].drop_duplicates(subset=["city","Main_Material_Code","total_floor_flag"])
data_remaining_durable = data_var["remaining_durable_table"].rename(columns={"Main_Material_Code":"Main_Material_Code_ref"})

# 讀取成交明細資料 (ap) 與內部資料 (ctbc)
data_ap = pd.read_csv(path_ap, sep="|", parse_dates=["DRPD_TradeDate","DRPD_CompletionDate"],dtype={"DRPD_ZipCode": str}, low_memory=False)
data_ctbc = pd.read_excel(join(path_landsplit, "ctbc_inside.xlsx"))

# 轉換Main_Material_Code為標準代碼及臨時代碼
data_ap["Main_Material_Code_temp"] = np.nan
# 對常見結構類型進行代碼歸類
data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("鋼骨|SRC|S．R．C", na=False), "Main_Material_Code_temp"] = 1
data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("鋼筋混凝土|RC|R．C", na=False) & data_ap["Main_Material_Code_temp"].isna(),"Main_Material_Code_temp"] = 2
data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("加強磚", na=False) & data_ap["Main_Material_Code_temp"].isna(), "Main_Material_Code_temp"]= 3
data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("鋼架", na=False) & data_ap["Main_Material_Code_temp"].isna(), "Main_Material_Code_temp"] =4
data_ap["Main_Material_Code_temp"].fillna(5, inplace=True) # 其他類型統一設為代碼5

# ctbc資料的建材代碼轉換（使用提供的對照字典）
data_ctbc["Main_Material_Code_ref"] = data_ctbc["Main_Material_Code"].map(lambda x: ctbc_mainmaterial_ref.get(x, x))
data_ctbc["Main_Material_Code_temp"] = data_ctbc["Main_Material_Code_ref"].map(lambda x: ctbc_mainmaterial_ref_temp.get(x, 2))

# 樓層區間標籤計算
data_ap["total_floor_flag"] = data_ap.apply(lambda row: assign_floor_flag(row["DRPD_TotalFloorFlag"], row["Main_Material_Code_temp"]), axis=1)
data_ctbc["total_floor_flag"] = data_ctbc.apply(lambda row: assign_floor_flag(row["Total_Floor_Cnt"], row["Main_Material_Code_temp"]), axis=1)

# 過濾無效資料點
data_ap = data_ap[(~data_ap["DRPD_MainPurpose"].isin([np.nan, "工業用", "其他", "農業用"])) & (data_ap["DRPD_NoteFlag"].isna()) &(data_ap["DRPD_TransFloorFlag"].between(2, 998))]
data_ctbc.replace(cityname_change, inplace=True, regex=True) # 標準化城市名稱
# 僅保留特定主建材類型且樓層不超過範圍的資料
data_ctbc = data_ctbc[data_ctbc["Main_Material_Code"].isin([1,2,3,4]) & (data_ctbc["total_floor_flag"] != "05.>10")]

# 建立時間篩選區間
start_date = pd.to_datetime("2025-04-01") # 可調整的起始日期
DateRange_ap = pd.date_range(start=start_date, periods=2, freq=pd.offsets.MonthBegin(6), inclusive='both')
DateRange_ctbc = pd.date_range(start=start_date, periods=6, freq='MS').strftime("%Y%m")

# 篩選近六個月的成交資料和內部資料
data_ap = data_ap[data_ap["DRPD_TradeDate"].between(DateRange_ap[0], DateRange_ap[1], inclusive="left")]
data_ctbc = data_ctbc[data_ctbc["Application_Nbr"].str.slice(0,6).isin(DateRange_ctbc)]

# ----3. 匯總市場成交價以獲取Seg分段----

# 計算不同層級上的房價中位數（單位價格）及樣本數
pivot_zip = data_ap.groupby(["DRPD_City", "DRPD_ZipCode"])["DRPD_UnitPriceRevised"].agg(median_price="median", count="size").reset_index()
pivot_floor = data_ap.groupby(["DRPD_City", "total_floor_flag"])["DRPD_UnitPriceRevised"].agg(median_price="median", count="size").reset_index()
pivot_city=data_ap.groupby("DRPD_City")["DRPD_UnitPriceRevised"].agg(median_price="median", count="size").reset_index()

# 根據最低樣本數門檻篩選可靠的統計
pivot_zip = pivot_zip[pivot_zip["count"] > MIN_GROUP_COUNT]
pivot_floor = pivot_floor[pivot_floor["count"] > MIN_GROUP_COUNT]
# city級不設門檻，確保每城市都有值

# 將中位數價格對應到建築成本區間(seg標籤)
pivot_zip["seg_final"] = pivot_zip.apply(lambda r: get_build_cost_seg(r["DRPD_City"], round(r["median_price"])), axis=1)
pivot_floor["seg_final"] = pivot_floor.apply(lambda r: get_build_cost_seg(r["DRPD_City"], round(r["median_price"])), axis=1)
pivot_city["seg_final"] = pivot_city.apply(lambda r: get_build_cost_seg(r["DRPD_City"], round(r["median_price"])), axis=1)

# 構建映射字典方便查找seg_final
seg_map_zip = pivot_zip.set_index(["DRPD_City", "DRPD_ZipCode"])["seg_final"].to_dict()
seg_map_floor = pivot_floor.set_index(["DRPD_City", "total_floor_flag"])["seg_final"].to_dict()
seg_map_city = pivot_city.set_index("DRPD_City")["seg_final"].to_dict()

# 將seg_final賦值給每筆ctbc案件：優先使用區段zip級，其次樓層級，最後城市級
def determine_seg_final(city, zip_code, floor_flag):
    # 依次嘗試細到粗粒度的seg估計
    if (city, zip_code) in seg_map_zip:
        return seg_map_zip[(city, zip_code)]
    elif (city, floor_flag) in seg_map_floor:
        return seg_map_floor[(city, floor_flag)]
    else:
        return seg_map_city.get(city, np.nan)

data_ctbc["seg_final"] = data_ctbc.apply(lambda r: determine_seg_final(r["After_five"], str(r["Area_Nbr"]), r["total_floor_flag"]), axis=1)

# 將seg_final結果補回建築成本表，用於後續上傳與檢查
data_buildcost_upload = data_buildcost_upload.merge(pivot_zip[["DRPD_City","DRPD_ZipCode","seg_final"]].rename(columns={"DRPD_City":"After_five","DRPD_ZipCode":"Area_Nbr"}),on=["After_five","Area_Nbr"], how="left")
data_buildcost_upload = data_buildcost_upload.merge(pivot_floor[["DRPD_City","total_floor_flag","seg_final"]].rename(columns={"DRPD_City":"After_five","seg_final":"seg_final_floor"}),on=["After_five","total_floor_flag"], how="left")
data_buildcost_upload = data_buildcost_upload.merge(pivot_city[["DRPD_City","seg_final"]].rename(columns={"DRPD_City":"After_five","seg_final":"seg_final_city"}),on="After_five", how="left")
# 按優先級填充缺失的seg_final
data_buildcost_upload["seg_final"] = data_buildcost_upload["seg_final"].fillna(data_buildcost_upload["seg_final_floor"])
data_buildcost_upload["seg_final"] = data_buildcost_upload["seg_final"].fillna(data_buildcost_upload["seg_final_city"])

# 生成唯一鍵與Seg_Index
data_buildcost_upload["Build_Cost_Key"] = data_buildcost_upload["Area_Nbr"] + "_" + data_buildcost_upload["total_floor_flag"].str[:2] + "_" +data_buildcost_upload["Main_Material_Code"].str.zfill(2)
data_buildcost_upload["Index"] = data_buildcost_upload["seg_final"].map(lambda x: seg_price_num.get(x, 1))
# 重新排列欄位順序
upload_cols = ["Build_Cost_Key"] + [f"segprice{i}" for i in range(1,10)] + ["Index"]
data_buildcost_upload = data_buildcost_upload.reindex(columns=upload_cols)

# ----4. 依Seg及耐久度計算最終單價----

# 取得每筆ctbc案件對應的seg單價 (以萬元為單位)
def lookup_seg_price(city, floor_flag, material_temp, seg_label):
    """從建築成本表中查詢指定區隔的單位價格(萬元)。"""
    rec = data_buildcost[(data_buildcost["city"]==city) & (data_buildcost["total_floor_flag"]==floor_flag) &(data_buildcost["Main_Material_Code"]==material_temp)]
    if rec.empty:
        return None
    price = rec.iloc[0][seg_label] # 該區隔的價格(元)
    return price / 10000 # 轉換為萬元

# 為ctbc資料查詢seg單價並合併
data_ctbc["seg_price_wan"] = data_ctbc.apply(lambda r: lookup_seg_price(r["After_five"], r["total_floor_flag"], r["Main_Material_Code_temp"], r["seg_final"]), axis=1)
# 合併建築工程總指數並轉換為倍率
data_ctbc = data_ctbc.merge(data_buildindex[["apply_date","buildindex"]], left_on=data_ctbc["Aprl_Date"].dt.to_period('M').dt.to_timestamp(), right_on="apply_date", how="left")
data_ctbc["build_index_factor"] = data_ctbc["buildindex"] / 100

# 耐久年限與殘值率
data_ctbc = data_ctbc.merge(data_remaining_durable[["Main_Material_Code_ref","remaining_rate","durable_year"]], on="Main_Material_Code_ref", how="left")
data_ctbc["remaining_year"] = data_ctbc["durable_year"] - data_ctbc["Building_Age"]

# 計算調整建物單價：seg單價 * 建築指數，再依屋齡折舊
data_ctbc["seg_price_adj"] = data_ctbc["seg_price_wan"] * data_ctbc["build_index_factor"]
# 四號公報計算: 耐用年限內直線折舊，耐用年限外取殘值
data_ctbc["final_price"] = np.where(data_ctbc["remaining_year"] > 0,# 耐用年限內
data_ctbc["seg_price_adj"] * (1 - (data_ctbc["Building_Age"] / data_ctbc["durable_year"]) * (1 - data_ctbc["remaining_rate"])),
# 耐用年限外
data_ctbc["seg_price_adj"] * data_ctbc["remaining_rate"])

# ----5. 多層級分組計算調整係數Var和Var2----

# 計算不同層級（細->粗）下，建物實際單價與模型預測單價的中位數比值和差值
groups = {
"level1": ["Area_Nbr", "total_floor_flag", "Building_Age_flag2"],
"level2": ["Area_Nbr", "Building_Age_flag2"],
"level3": ["Area_Nbr"],
"level4": ["County"]
}
var_results = {}
for level, keys in groups.items():
    agg = data_ctbc.groupby(keys).agg(median_buildprice=("BuildPrice","median"),median_modelprice=("final_price","median"),count=("Application_Nbr","size")).reset_index()
    # 過濾樣本數不足的組合（僅對較細緻層級做限制）
    if level in ["level1","level2","level3"]:
        agg = agg[agg["count"] > MIN_GROUP_COUNT]
    agg["Var"] = agg["median_buildprice"] / agg["median_modelprice"]
    agg["Var2"] = agg["median_buildprice"] - agg["median_modelprice"]
    var_results[level] = agg

# 將Var和Var2按層級依次合併到主資料，並記錄採用的層級
data_ctbc["Var"] = np.nan
data_ctbc["Var2"] = np.nan
data_ctbc["Var_level"] = np.nan
for level, keys in groups.items():
    data_ctbc = data_ctbc.merge(var_results[level][keys + ["Var","Var2"]], on=keys, how="left", suffixes=(None, f"_{level}"))
    # 若尚未填入值且該層級有值，則使用之
    fill_mask = data_ctbc["Var"].isna() & ~data_ctbc[f"Var_{level}"].isna()
    data_ctbc.loc[fill_mask, "Var"] = data_ctbc.loc[fill_mask, f"Var_{level}"]
    data_ctbc.loc[fill_mask, "Var2"] = data_ctbc.loc[fill_mask, f"Var2_{level}"]
    data_ctbc.loc[fill_mask, "Var_level"] = level

# 如仍有缺失（極端情況），以1（無調整）填充
data_ctbc["Var"].fillna(1, inplace=True)
data_ctbc["Var2"].fillna(0, inplace=True)

# 將Var和Var2離散化為標準刻度（Var取0.2為刻度，Var2取0.5為刻度）
def round_to_step(x, step):
    return round(step * round(x/step, 0), 1)

data_ctbc["Var"] = data_ctbc["Var"].astype(float).map(lambda x: round_to_step(x, 0.2))
data_ctbc["Var2"] = data_ctbc["Var2"].astype(float).map(lambda x: round_to_step(x, 0.5))

# ----6. 計算兩種調整後的建物價格(final_price_adj, final_price_adj2)----

# final_price_adj: 按比例調整(倍數修正)
data_ctbc["final_price_adj"] = np.where(data_ctbc["remaining_year"] > 0,data_ctbc["final_price"] * data_ctbc["Var"],data_ctbc["final_price"] # 超過耐用年限則不再乘調整倍數
)
# final_price_adj2: 按平移調整(金額修正)
data_ctbc["final_price_adj2"] = np.where(data_ctbc["remaining_year"] > 0,data_ctbc["final_price"] + data_ctbc["Var2"],data_ctbc["final_price"] # 超過耐用年限則不加固定值
)

# 特殊區域最低價格限制調整
mask_special = data_ctbc["After_five"].isin(SPECIAL_REGIONS)
mask_general = ~data_ctbc["After_five"].isin(SPECIAL_REGIONS)
# 新屋或壽命未滿，以及壽命剛過的建物
cond_new = data_ctbc["remaining_year"] > 0
cond_just_expired = data_ctbc["remaining_year"].between(-3, 0)
# 壽命超過一定年限的建物
cond_mid_expired = data_ctbc["remaining_year"].between(-9, -4)
cond_long_expired = data_ctbc["remaining_year"] <= -10

# 在特殊區域，設定最低門檻值
data_ctbc.loc[(mask_special & (cond_new | cond_just_expired) & (data_ctbc["final_price_adj2"] < 3)), "final_price_adj2"] = 3
data_ctbc.loc[(mask_special & cond_mid_expired & (data_ctbc["final_price_adj2"] < 2.5)), "final_price_adj2"] = 2.5
data_ctbc.loc[(mask_special & cond_long_expired & (data_ctbc["final_price_adj2"] < 1.5)), "final_price_adj2"] = 1.5
# 在非特殊區域，設定另外的最低門檻值
data_ctbc.loc[(mask_general & (cond_new | cond_just_expired) & (data_ctbc["final_price_adj2"] < 1)), "final_price_adj2"] = 1
data_ctbc.loc[(mask_general & cond_mid_expired & (data_ctbc["final_price_adj2"] < 0.8)), "final_price_adj2"] = 0.8
data_ctbc.loc[(mask_general & cond_long_expired & (data_ctbc["final_price_adj2"] < 0.5)), "final_price_adj2"] = 0.5

# ----7. 結果輸出----

# 計算與實際建物單價的差異，用於檢查誤差分布（MAPE）
data_ctbc["diff_final"] = data_ctbc["final_price"] - data_ctbc["BuildPrice"]
data_ctbc["diff_adj"] = data_ctbc["final_price_adj"] - data_ctbc["BuildPrice"]
data_ctbc["diff_adj2"] = data_ctbc["final_price_adj2"] - data_ctbc["BuildPrice"]
data_ctbc["MAPE_final"] = (data_ctbc["diff_final"] / data_ctbc["BuildPrice"]).abs()
data_ctbc["MAPE_adj"] = (data_ctbc["diff_adj"] / data_ctbc["BuildPrice"]).abs()
data_ctbc["MAPE_adj2"] = (data_ctbc["diff_adj2"] / data_ctbc["BuildPrice"]).abs()

# 將結果保存至Excel檔案
with pd.ExcelWriter(join(path_landsplit, f"Build_Cost_Table_{today_str}.xlsx")) as writer:
    data_buildcost_upload.to_excel(writer, sheet_name="upload", index=False)
    # 亦可輸出更多資訊以供檢查，如中間計算結果
    data_ctbc.to_excel(writer, sheet_name="result_detail", index=False)
