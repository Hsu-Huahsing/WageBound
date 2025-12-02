# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 17:14:13 2024

@author: Z00051711
"""

from ctbc_project.config import checkinterval, colname, maxlength
from os.path import join
from numpy import nan

import pandas as pd

def interval_get(value = 0):
    for key in checkinterval:
        # print(key)
        # print(value)
        # print(type(value))
        # print(int(value))
        if int(float(value)) in checkinterval[key]:
            # print(value,"++++++++++++")
            # print(checkinterval[key])
            return key
        else :
            '99.Else'
        # else:
            # print(value,"===========")
            
def len_str(x):
    if pd.isnull(x) is True :
        return 0
    else:
        return len(str(x))

month = pd.date_range("2025-10", periods=2, freq="MS") #月份要加1,如果是3月底作資料，這裡要寫2，會比當月扣1

file_name = r"GEOM_CTBC_RealPriceDetail_stall.csv"
file_name_old = r"GEOM_CTBC_RealPriceDetail.csv"

path_wb = r"D:\DGIS\workbench"
path_zipcode = r"D:\DGIS\ZIP.xlsx"
path = join(path_wb, month[1].strftime("%Y%m"), file_name)
path_old = join(path_wb, month[1].strftime("%Y%m"), file_name_old)
path_last = join(path_wb, month[0].strftime("%Y%m"), file_name)
path_ttl = join(path_wb, month[1].strftime("%Y%m"), "GEOM_CTBC_RealPriceDetail.pkl")
path_building = join(path_wb, month[1].strftime("%Y%m"), "building.pkl")
res = {}

# 先改名=======================================================================
# GEOM_CTBC_RealPriceDetail_20240826_resAddonAll.csv 改成 GEOM_CTBC_RealPriceDetail_DGIS.csv
# GEOM_CTBC_RealPriceDetail_20240826_resAddonPart.csv 改成 GEOM_CTBC_RealPriceDetail_stall.csv 上傳FTP的時候要改成 GEOM_CTBC_RealPriceDetail.csv
# 實價不動產買賣_output_2024-08-22 17_39_20_651811.pkl 改成 GEOM_CTBC_RealPriceDetail.pkl
# 實價建物_output_2024-08-22 17_53_40_852560.pkl 改成 building.pkl
# =============================================================================
df_len = pd.DataFrame()
file = pd.read_csv(path,dtype=str, sep="|", encoding='utf8' )
file_last = pd.read_csv(path_last,dtype=str, sep="|", encoding='utf8' )
file_zipcode = pd.read_excel(path_zipcode, dtype=str).rename(columns={'city':'DRPD_City','town':'DRPD_District',"zip":"zip_check"})
# check = pd.Series([file.shape[0],100,file_last.shape[0],100])
# =============================================================================
# file=file.rename(columns={"CommunityFlag":"DRPD_CommunityFlag"})
# file.to_csv(path, sep="|", index = False, encoding = 'utf8')

temp1 = file.loc[file["DRPD_Sequence"].duplicated(keep=False) | file["DRPD_Sequence"].isna(),:]
if temp1.empty is True :
    res["DRPD_Sequence"] = ["Y", temp1.shape]
else :
    print("DRPD_Sequence ERROR !")
# =============================================================================
# =============================================================================

temp2 = file.loc[~file["Geom"].isna(),:]
if temp2.empty is True :
    res["Geom"] = ["Y", temp2.shape]
else :
    print("Geom ERROR !")
# =============================================================================
# =============================================================================

temp4 = file.loc[file["DRPD_City"].isna(),:]
if temp4.empty is True :
    res["DRPD_City"] = ["Y", temp4.shape]
else :
    print("DRPD_City ERROR !")
# =============================================================================
# =============================================================================

temp5 = file.loc[file["DRPD_District"].isna(),:]
if temp5.empty is True :
    res["DRPD_District"] = ["Y", temp5.shape]
else :
    print("DRPD_District ERROR !")
# =============================================================================
# =============================================================================

temp3 = pd.merge(file, file_zipcode,how="left",on=['DRPD_City','DRPD_District'])
temp3 = temp3.loc[(temp3["DRPD_ZipCode"]!=temp3["zip_check"])|temp3["DRPD_ZipCode"].isna(),:]
if temp3.empty is True :
    res["DRPD_ZipCode"] = ["Y", temp3.shape]
else :
    print("DRPD_ZipCode ERROR !")
# =============================================================================
# =============================================================================

temp6 = file.loc[file["DRPD_TradeTarget"].isna()|file["DRPD_TradeTarget"]=="土地",:]
# file_ttl.loc[file_ttl["Trading_Target"].isna(),:]
if temp6.empty is True :
    res["DRPD_TradeTarget"] = ["Y", temp6.shape]
else :
    print("DRPD_TradeTarget ERROR !")
# =============================================================================
# =============================================================================

temp7 = file.loc[file["DRPD_Address"].isna() | (file["DRPD_Address"].apply(lambda x : len(x))>30),:]
if temp7.empty is True :
    res["DRPD_Address"] = ["Y", temp7.shape]
else :
    print("DRPD_Address ERROR !")
# =============================================================================
# =============================================================================

interval1 = file.loc[:,["DRPD_LandTransArea"]]
interval2 = file_last.loc[:,["DRPD_LandTransArea"]]

interval1["interval"] = interval1["DRPD_LandTransArea"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_LandTransArea"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_LandTransArea"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_LandTransArea"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp8 = interval3-interval4
interval3.columns = ["thismonth","thismonth"]
interval4.columns = ["lastmonth","lastmonth"]
temp8 = pd.concat([ interval3,interval4, temp8],axis=1)
temp8 = pd.concat([temp8, pd.DataFrame(temp8.sum(),columns=["SUM"]).T],axis=0)

# =============================================================================
# =============================================================================
temp9 = file["DRPD_LandUseType"].unique()
file["DRPD_LandUseType"].dtype
if str(file["DRPD_LandUseType"].dtype) == "object" :
    res["DRPD_LandUseType"] = "Y"
else :
    print("DRPD_LandUseType ERROR !")
# =============================================================================
# =============================================================================
temp10 = file["DRPD_NonUrbanDistrict"].unique()
file["DRPD_NonUrbanDistrict"].dtype
if str(file["DRPD_NonUrbanDistrict"].dtype) == "object" :
    res["DRPD_NonUrbanDistrict"] = "Y"
else :
    print("DRPD_NonUrbanDistrict ERROR !")
# =============================================================================
# =============================================================================
temp11 = file["DRPD_NonUrbanland"].unique()
file["DRPD_NonUrbanland"].dtype
if str(file["DRPD_NonUrbanland"].dtype) == "object" :
    res["DRPD_NonUrbanland"] = "Y"
else :
    print("DRPD_NonUrbanland ERROR !")
# =============================================================================
# =============================================================================
temp12 = [file["DRPD_TradeDate"].max(),file["DRPD_TradeDate"].min()]
file["DRPD_TradeDate"].dtype
if str(file["DRPD_TradeDate"].dtype) == "object" :
    res["DRPD_TradeDate"] = ["Y"] + temp12
else :
    print("DRPD_TradeDate ERROR !")
# =============================================================================
# =============================================================================
temp13 = file.loc[file["DRPD_Transactions"].isna(),:]
if temp13.empty is True :
    res["DRPD_Transactions"] = ["Y", temp13.shape]
else :
    print("DRPD_Transactions ERROR !")
# =============================================================================
# =============================================================================
temp14 = file["DRPD_TransFloor"].unique()
file["DRPD_TransFloor"].dtype
if str(file["DRPD_TransFloor"].dtype) == "object" :
    res["DRPD_TransFloor"] = "Y"
else :
    print("DRPD_TransFloor ERROR !")
# =============================================================================
# =============================================================================
temp15 = file["DRPD_TotalFloor"].unique()
file["DRPD_TotalFloor"].dtype
if str(file["DRPD_TotalFloor"].dtype) == "object" :
    res["DRPD_TotalFloor"] = "Y"
else :
    print("DRPD_TotalFloor ERROR !")
# =============================================================================
# =============================================================================
temp16 = file.loc[file["DRPD_BuildingType"].isna(),:]
if temp16.empty is True :
    res["DRPD_BuildingType"] = ["Y", temp16.shape]
else :
    print("DRPD_BuildingType ERROR !")
# =============================================================================
# =============================================================================

interval1 = file.groupby(["DRPD_BuildingTypeFlag"])["DRPD_BuildingTypeFlag"].count().sort_index()
interval2 = file_last.groupby(["DRPD_BuildingTypeFlag"])["DRPD_BuildingTypeFlag"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp17 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp17 = pd.concat([ interval3,interval4, temp17],axis=1)
temp17 = pd.concat([temp17, pd.DataFrame(temp17.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
temp18 = file["DRPD_MainPurpose"].unique()
file["DRPD_MainPurpose"].dtype
if str(file["DRPD_MainPurpose"].dtype) == "object" :
    res["DRPD_MainPurpose"] = "Y"
else :
    print("DRPD_MainPurpose ERROR !")
# =============================================================================
# =============================================================================
temp19 = file["DRPD_MainMaterial"].unique()
file["DRPD_MainMaterial"].dtype
if str(file["DRPD_MainMaterial"].dtype) == "object" :
    res["DRPD_MainMaterial"] = "Y"
else :
    print("DRPD_MainMaterial ERROR !")
# =============================================================================
# =============================================================================
temp20 = file["DRPD_CompletionDate"].unique()
file["DRPD_CompletionDate"].dtype
if str(file["DRPD_CompletionDate"].dtype) == "object" :
    res["DRPD_CompletionDate"] = "Y"
else :
    print("DRPD_CompletionDate ERROR !")
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_TransArea"]]
interval2 = file_last.loc[:,["DRPD_TransArea"]]

interval1["interval"] = interval1["DRPD_TransArea"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_TransArea"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_TransArea"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_TransArea"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp21 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp21 = pd.concat([ interval3,interval4, temp21],axis=1)
temp21 = pd.concat([temp21, pd.DataFrame(temp21.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
temp22 = file.loc[file["DRPD_LayoutBedroom"].isna(),:]
if temp22.empty is True :
    res["DRPD_LayoutBedroom"] = ["Y", temp22.shape]
else :
    print("DRPD_LayoutBedroom ERROR !")
# =============================================================================
# =============================================================================
temp23 = file.loc[file["DRPD_LayoutLivroom"].isna(),:]
if temp23.empty is True :
    res["DRPD_LayoutLivroom"] = ["Y", temp23.shape]
else :
    print("DRPD_LayoutLivroom ERROR !")
# =============================================================================
# =============================================================================
temp24 = file.loc[file["DRPD_LayoutBathroom"].isna(),:]
if temp24.empty is True :
    res["DRPD_LayoutBathroom"] = ["Y", temp24.shape]
else :
    print("DRPD_LayoutBathroom ERROR !")
# =============================================================================
# =============================================================================
# interval要檢查不能包含null值
interval1 = file.groupby(["DRPD_Partition"])["DRPD_Partition"].count().sort_index()
interval2 = file_last.groupby(["DRPD_Partition"])["DRPD_Partition"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp25 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp25 = pd.concat([ interval3,interval4, temp25],axis=1)
temp25 = pd.concat([temp25, pd.DataFrame(temp25.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
# interval要檢查不能包含null值
interval1 = file.groupby(["DRPD_Management"])["DRPD_Management"].count().sort_index()
interval2 = file_last.groupby(["DRPD_Management"])["DRPD_Management"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp26 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp26 = pd.concat([ interval3,interval4, temp26],axis=1)
temp26 = pd.concat([temp26, pd.DataFrame(temp26.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_TotalPrice"]]
interval2 = file_last.loc[:,["DRPD_TotalPrice"]]

interval1["interval"] = interval1["DRPD_TotalPrice"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_TotalPrice"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_TotalPrice"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_TotalPrice"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp27 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp27 = pd.concat([ interval3,interval4, temp27],axis=1)
temp27 = pd.concat([temp27, pd.DataFrame(temp27.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_UnitPrice"]]
interval2 = file_last.loc[:,["DRPD_UnitPrice"]]

interval1["interval"] = interval1["DRPD_UnitPrice"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_UnitPrice"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_UnitPrice"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_UnitPrice"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp28 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp28 = pd.concat([ interval3,interval4, temp28],axis=1)
temp28 = pd.concat([temp28, pd.DataFrame(temp28.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_UnitPriceRevised"]]
interval2 = file_last.loc[:,["DRPD_UnitPriceRevised"]]

interval1["interval"] = interval1["DRPD_UnitPriceRevised"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_UnitPriceRevised"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_UnitPriceRevised"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_UnitPriceRevised"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp29 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp29 = pd.concat([ interval3,interval4, temp29],axis=1)
temp29 = pd.concat([temp29, pd.DataFrame(temp29.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_StallTotalPriceProxy"]]
interval2 = file_last.loc[:,["DRPD_StallTotalPriceProxy"]]

interval1["interval"] = interval1["DRPD_StallTotalPriceProxy"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_StallTotalPriceProxy"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_StallTotalPriceProxy"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_StallTotalPriceProxy"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp30 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp30 = pd.concat([ interval3,interval4, temp30],axis=1)
temp30 = pd.concat([temp30, pd.DataFrame(temp30.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
# interval要檢查不能包含null值
interval1 = file.groupby(["DRPD_Management"])["DRPD_RealEstateStallFlag"].count().sort_index()
interval2 = file_last.groupby(["DRPD_Management"])["DRPD_RealEstateStallFlag"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp31 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp31 = pd.concat([ interval3,interval4, temp31],axis=1)
temp31 = pd.concat([temp31, pd.DataFrame(temp31.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_StallCnt"]]
interval2 = file_last.loc[:,["DRPD_StallCnt"]]

interval1["interval"] = interval1["DRPD_StallCnt"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_StallCnt"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_StallCnt"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_StallCnt"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp32 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp32 = pd.concat([ interval3,interval4, temp32],axis=1)
temp32 = pd.concat([temp32, pd.DataFrame(temp32.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_StallTransArea"]]
interval2 = file_last.loc[:,["DRPD_StallTransArea"]]

interval1["interval"] = interval1["DRPD_StallTransArea"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_StallTransArea"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_StallTransArea"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_StallTransArea"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp33 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp33 = pd.concat([ interval3,interval4, temp33],axis=1)
temp33 = pd.concat([temp33, pd.DataFrame(temp33.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_StallTotalPrice"]]
interval2 = file_last.loc[:,["DRPD_StallTotalPrice"]]

interval1["interval"] = interval1["DRPD_StallTotalPrice"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_StallTotalPrice"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_StallTotalPrice"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_StallTotalPrice"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp34 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp34 = pd.concat([ interval3,interval4, temp34],axis=1)
temp34 = pd.concat([temp34, pd.DataFrame(temp34.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
# 產生keyerror是正常的，代表沒有1這個欄位，就是沒有小數點可以切
temp35 = file["DRPD_TargetX"].astype(str).str.split(".",expand=True)[1]
res["DRPD_TargetX"] = "Y"
# =============================================================================
# =============================================================================
# 產生keyerror是正常的，代表沒有1這個欄位，就是沒有小數點可以切
temp36 = file["DRPD_TargetY"].astype(str).str.split(".",expand=True)[1]
res["DRPD_TargetY"] = "Y"
# =============================================================================
# =============================================================================
interval1 = file.groupby(["DRPD_HasNote"])["DRPD_HasNote"].count().sort_index()
interval2 = file_last.groupby(["DRPD_HasNote"])["DRPD_HasNote"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp37 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp37 = pd.concat([ interval3,interval4, temp37],axis=1)
temp37 = pd.concat([temp37, pd.DataFrame(temp37.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
temp38 = file["DRPD_Note"].unique()
file["DRPD_Note"].dtype
if str(file["DRPD_Note"].dtype) == "object" :
    res["DRPD_Note"] = "Y"
else :
    print("DRPD_Note ERROR !")
# =============================================================================
# =============================================================================
interval1 = file.groupby(["DRPD_SpecialTradeFlag"])["DRPD_SpecialTradeFlag"].count().sort_index()
interval2 = file_last.groupby(["DRPD_SpecialTradeFlag"])["DRPD_SpecialTradeFlag"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp39 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp39 = pd.concat([ interval3,interval4, temp39],axis=1)
temp39 = pd.concat([temp39, pd.DataFrame(temp39.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
temp40 = file.loc[file["DRPD_Number"].duplicated(keep=False) | file["DRPD_Number"].isna(),:]
if temp40.empty is True :
    res["DRPD_Number"] = ["Y", temp40.shape]
else :
    print("DRPD_Number ERROR !")
# =============================================================================
# =============================================================================
# 看0的比率不要超過5%
interval1 = file.groupby(["DRPD_FishId"])["DRPD_FishId"].count().sort_index()
interval2 = file_last.groupby(["DRPD_FishId"])["DRPD_FishId"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp41 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp41 = pd.concat([ interval3,interval4, temp41],axis=1)
temp41 = pd.concat([temp41, pd.DataFrame(temp41.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.groupby(["DRPD_BuildingSeg"])["DRPD_BuildingSeg"].count().sort_index()
interval2 = file_last.groupby(["DRPD_BuildingSeg"])["DRPD_BuildingSeg"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp42 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp42 = pd.concat([ interval3,interval4, temp42],axis=1)
temp42 = pd.concat([temp42, pd.DataFrame(temp42.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_BuildingAge"]]
interval2 = file_last.loc[:,["DRPD_BuildingAge"]]

interval1["interval"] = interval1["DRPD_BuildingAge"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_BuildingAge"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_BuildingAge"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_BuildingAge"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp43 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp43 = pd.concat([ interval3,interval4, temp43],axis=1)
temp43 = pd.concat([temp43, pd.DataFrame(temp43.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_GParking"]]
interval2 = file_last.loc[:,["DRPD_GParking"]]

interval1["interval"] = interval1["DRPD_GParking"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_GParking"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_GParking"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_GParking"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp44 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp44 = pd.concat([ interval3,interval4, temp44],axis=1)
temp44 = pd.concat([temp44, pd.DataFrame(temp44.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_EParking"]]
interval2 = file_last.loc[:,["DRPD_EParking"]]

interval1["interval"] = interval1["DRPD_EParking"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_EParking"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_EParking"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_EParking"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp45 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp45 = pd.concat([ interval3,interval4, temp45],axis=1)
temp45 = pd.concat([temp45, pd.DataFrame(temp45.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_GParkingPrice"]]
interval2 = file_last.loc[:,["DRPD_GParkingPrice"]]

interval1["interval"] = interval1["DRPD_GParkingPrice"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_GParkingPrice"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_GParkingPrice"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_GParkingPrice"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp46 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp46 = pd.concat([ interval3,interval4, temp46],axis=1)
temp46 = pd.concat([temp46, pd.DataFrame(temp46.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_EParkingPrice"]]
interval2 = file_last.loc[:,["DRPD_EParkingPrice"]]

interval1["interval"] = interval1["DRPD_EParkingPrice"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_EParkingPrice"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_EParkingPrice"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_EParkingPrice"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp47 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp47 = pd.concat([ interval3,interval4, temp47],axis=1)
temp47 = pd.concat([temp47, pd.DataFrame(temp47.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.groupby(["DRPD_ModifyFlag"])["DRPD_ModifyFlag"].count().sort_index()
interval2 = file_last.groupby(["DRPD_ModifyFlag"])["DRPD_ModifyFlag"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp48 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp48 = pd.concat([ interval3,interval4, temp48],axis=1)
temp48 = pd.concat([temp48, pd.DataFrame(temp48.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
temp49 = file["DRPD_BuildingName"].unique()
file["DRPD_BuildingName"].dtype
if str(file["DRPD_BuildingName"].dtype) == "object" :
    res["DRPD_BuildingName"] = "Y"
else :
    print("DRPD_BuildingName ERROR !")
# =============================================================================
# =============================================================================
temp50 = file["DRPD_BuildingKey"].unique()
file["DRPD_BuildingKey"].dtype
if str(file["DRPD_BuildingKey"].dtype) == "object" :
    res["DRPD_BuildingKey"] = "Y"
else :
    print("DRPD_BuildingKey ERROR !")
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_TransFloorFlag"]]
interval2 = file_last.loc[:,["DRPD_TransFloorFlag"]]

interval1["interval"] = interval1["DRPD_TransFloorFlag"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_TransFloorFlag"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_TransFloorFlag"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_TransFloorFlag"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp51 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp51 = pd.concat([ interval3,interval4, temp51],axis=1)
temp51 = pd.concat([temp51, pd.DataFrame(temp51.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
temp52 = file["DRPD_NoteFlag"].unique()
file["DRPD_NoteFlag"].dtype
if str(file["DRPD_NoteFlag"].dtype) == "object" :
    res["DRPD_NoteFlag"] = "Y"
else :
    print("DRPD_NoteFlag ERROR !")
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_BuildingArea"]]
interval2 = file_last.loc[:,["DRPD_BuildingArea"]]

interval1["interval"] = interval1["DRPD_BuildingArea"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_BuildingArea"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_BuildingArea"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_BuildingArea"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp53 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp53 = pd.concat([ interval3,interval4, temp53],axis=1)
temp53 = pd.concat([temp53, pd.DataFrame(temp53.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.groupby(["DRPD_OutlierTxn"])["DRPD_OutlierTxn"].count().sort_index()
interval2 = file_last.groupby(["DRPD_OutlierTxn"])["DRPD_OutlierTxn"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp54 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp54 = pd.concat([ interval3,interval4, temp54],axis=1)
temp54 = pd.concat([temp54, pd.DataFrame(temp54.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
temp55 = file.loc[file["DRPD_RoadSecName"].apply(lambda x : len(str(x)))>20,:]
if temp55.empty is True :
    res["DRPD_RoadSecName"] =  ["Y", temp55.shape]
else :
    print("DRPD_RoadSecName ERROR !")
# =============================================================================
# =============================================================================
temp56 = file.loc[file["DRPD_AlleyName"].apply(lambda x : len(str(x)))>20,:]
if temp56.empty is True :
    res["DRPD_AlleyName"] = ["Y", temp56.shape]
else :
    print("DRPD_AlleyName ERROR !")
# =============================================================================
# =============================================================================
interval1 = file.groupby(["DRPD_IsAlley"])["DRPD_IsAlley"].count().sort_index()
interval2 = file_last.groupby(["DRPD_IsAlley"])["DRPD_IsAlley"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp57 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp57 = pd.concat([ interval3,interval4, temp57],axis=1)
temp57 = pd.concat([temp57, pd.DataFrame(temp57.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.loc[:,["DRPD_TotalFloorFlag"]]
interval2 = file_last.loc[:,["DRPD_TotalFloorFlag"]]

interval1["interval"] = interval1["DRPD_TotalFloorFlag"].apply(lambda x : interval_get(x))
interval2["interval"] = interval2["DRPD_TotalFloorFlag"].apply(lambda x : interval_get(x))

interval1 = interval1.groupby(["interval"])["DRPD_TotalFloorFlag"].count().sort_index()
interval2 = interval2.groupby(["interval"])["DRPD_TotalFloorFlag"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp58 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp58 = pd.concat([ interval3,interval4, temp58],axis=1)
temp58 = pd.concat([temp58, pd.DataFrame(temp58.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# =============================================================================
interval1 = file.groupby(["DRPD_CommunityFlag"])["DRPD_CommunityFlag"].count().sort_index()
interval2 = file_last.groupby(["DRPD_CommunityFlag"])["DRPD_CommunityFlag"].count().sort_index()

interval3 = pd.concat([interval1,(interval1/interval1.sum())*100],axis=1)
interval4 = pd.concat([interval2,(interval2/interval2.sum())*100],axis=1)

temp59 = interval3-interval4
interval3.columns = ["thismonth_cnt","thismonth_%"]
interval4.columns = ["lastmonth_cnt","lastmonth_%"]
temp59 = pd.concat([ interval3,interval4, temp59],axis=1)
temp59 = pd.concat([temp59, pd.DataFrame(temp59.sum(),columns=["SUM"]).T],axis=0)
# =============================================================================
# 以上資料變動檢核結束
# 以下開始做資料長度檢核

temp60 = pd.DataFrame([maxlength],index=["max"])
data_len = {}
for key in maxlength:
    temp = file[key].apply(lambda x : len_str(x))
    temp_max_len = max(temp)
    data_len[key] = temp_max_len
temp60 = pd.concat([pd.DataFrame([data_len],index=["data_length"]),temp60]).T
temp60["diff"] = temp60["max"] - temp60["data_length"]
# 以上長度檢核結束
# =============================================================================
res = pd.DataFrame([res])

with pd.ExcelWriter(join(path_wb, month[1].strftime("%Y%m"), "CheckResult_Python.xlsx")) as writer :
    res.to_excel(writer, sheet_name='check', index=False, engine='xlsxwriter')
    temp60.to_excel(writer, sheet_name='length', index=True, engine='xlsxwriter')
    temp8.to_excel(writer, sheet_name='DRPD_LandTransArea', index=True, engine='xlsxwriter')
    temp17.to_excel(writer, sheet_name='DRPD_BuildingTypeFlag', index=True, engine='xlsxwriter')
    temp21.to_excel(writer, sheet_name='DRPD_TransArea', index=True, engine='xlsxwriter')
    temp25.to_excel(writer, sheet_name='DRPD_Partition', index=True, engine='xlsxwriter')
    temp26.to_excel(writer, sheet_name='DRPD_Management', index=True, engine='xlsxwriter')
    temp27.to_excel(writer, sheet_name='DRPD_TotalPrice', index=True, engine='xlsxwriter')
    temp28.to_excel(writer, sheet_name='DRPD_UnitPrice', index=True, engine='xlsxwriter')
    temp29.to_excel(writer, sheet_name='DRPD_UnitPriceRevised', index=True, engine='xlsxwriter')
    temp30.to_excel(writer, sheet_name='DRPD_StallTotalPriceProxy', index=True, engine='xlsxwriter')
    temp31.to_excel(writer, sheet_name='DRPD_RealEstateStallFlag', index=True, engine='xlsxwriter')
    temp32.to_excel(writer, sheet_name='DRPD_StallCnt', index=True, engine='xlsxwriter')
    temp33.to_excel(writer, sheet_name='DRPD_StallTransArea', index=True, engine='xlsxwriter')
    temp34.to_excel(writer, sheet_name='DRPD_StallTotalPrice', index=True, engine='xlsxwriter')
    temp37.to_excel(writer, sheet_name='DRPD_HasNote', index=True, engine='xlsxwriter')
    temp39.to_excel(writer, sheet_name='DRPD_SpecialTradeFlag', index=True, engine='xlsxwriter')
    temp41.to_excel(writer, sheet_name='DRPD_FishId', index=True, engine='xlsxwriter')
    temp42.to_excel(writer, sheet_name='DRPD_BuildingSeg', index=True, engine='xlsxwriter')
    temp43.to_excel(writer, sheet_name='DRPD_BuildingAge', index=True, engine='xlsxwriter')
    temp44.to_excel(writer, sheet_name='DRPD_GParking', index=True, engine='xlsxwriter')
    temp45.to_excel(writer, sheet_name='DRPD_EParking', index=True, engine='xlsxwriter')
    temp46.to_excel(writer, sheet_name='DRPD_GParkingPrice', index=True, engine='xlsxwriter')
    temp47.to_excel(writer, sheet_name='DRPD_EParkingPrice', index=True, engine='xlsxwriter')
    temp48.to_excel(writer, sheet_name='DRPD_ModifyFlag', index=True, engine='xlsxwriter')
    temp51.to_excel(writer, sheet_name='DRPD_TransFloorFlag', index=True, engine='xlsxwriter')
    temp53.to_excel(writer, sheet_name='DRPD_BuildingArea', index=True, engine='xlsxwriter')
    temp54.to_excel(writer, sheet_name='DRPD_OutlierTxn', index=True, engine='xlsxwriter')
    temp57.to_excel(writer, sheet_name='DRPD_IsAlley', index=True, engine='xlsxwriter')
    temp58.to_excel(writer, sheet_name='DRPD_TotalFloorFlag', index=True, engine='xlsxwriter')
    temp59.to_excel(writer, sheet_name='DRPD_CommunityFlag', index=True, engine='xlsxwriter')

file["DRPD_CommunityFlag"].value_counts()

# file_ttl = pickleload(path_ttl)
file_ttl = pd.read_pickle(path_ttl)
file_building = pd.read_pickle(path_building)

file_ttl = file_ttl.drop(columns = ["Unnamed: 35"], errors="ignore")
# 歷年資料未加工要確定欄位數只能有36
# file_building要確定欄位數只能有11
# DGIS加工過的要確認欄位數有59

file_building = file_building.loc[file_building["編號"].isin(file["DRPD_Number"]),:]
file_building = file_building.rename(columns=colname["建物"])

def strtodate(x):
    # 0820412轉成1993/04/12
    if pd.isna(x) is True:
        return
    # print(x)
    x = str(x).split(".")[0]
    # print(x)
    x = x.replace(" ","").replace('-','')
    # print(x)
    if 7>= len(x) >= 6:
        x = str(x).zfill(7)
    else:
        return
    
    d = x[-2:]
    m = x[-4:-2]
    y = str(int(x[:-4])+1911)
    
    if d == "00":
        d = "01"
    if m == "00":
        m = "01"
    
    res = pd.to_datetime("-".join([y,m,d]), errors="coerce")

    if pd.isna(res) is True:
        return 
    else:
        return res.strftime("%Y/%m/%d")

file_ttl = file_ttl.rename(columns=colname["不動產買賣"])

# 下面這一段是跑測試，如果有日期轉換失敗，才需要跑=============================================================================
a = file_ttl.loc[file_ttl["Completion_Date"].str.contains("-",regex=True,na=False),:]
a.loc[:,['Trading_Date','Completion_Date']] = a[['Trading_Date','Completion_Date']].map(lambda x : strtodate(x))
# 測試結束=============================================================================

file_ttl.loc[:,['Trading_Date','Completion_Date']] = file_ttl[['Trading_Date','Completion_Date']].map(lambda x : strtodate(x))

file_ttl.to_csv(join(path_wb, month[1].strftime("%Y%m"),file_name_old), sep="|", index = False, encoding = 'utf8')
file_building.to_csv(join(path_wb, month[1].strftime("%Y%m"),"building.csv"), sep="|", index = False, encoding = 'utf8')
# =============================================================================
# =============================================================================
# =============================================================================
# 上傳出錯檢查用
path_upload_last = join(path_wb, month[0].strftime("%Y%m"),r"上傳DGIS", file_name_old)
file_upload_last = pd.read_csv(path_upload_last,dtype=str, sep="|", encoding='utf8' )
check_dict_last = {}
check_nan_last = {}
check_float_last = {}

for key_name in file_upload_last :
    check_dict_last[key_name] = file_upload_last[key_name].unique()
    
    if nan in check_dict_last[key_name].tolist() :
        check_nan_last[key_name] = "Y"
    elif nan not in check_dict_last[key_name].tolist() :
        check_nan_last[key_name] = "N"
        
    try:
        file_upload_last[key_name].astype(float)
        check_float_last[key_name] = "Y"
    except:
        check_float_last[key_name] = "N"
    
path_upload = join(path_wb, month[1].strftime("%Y%m"),r"上傳DGIS", file_name_old)
file_upload = pd.read_csv(path_upload,dtype=str, sep="|", encoding='utf8' )
check_dict = {}
check_nan = {}
check_float = {}

for key_name in file_upload :
    check_dict[key_name] = file_upload[key_name].unique()
    
    if nan in check_dict[key_name].tolist() :
        check_nan[key_name] = "Y"
    elif nan not in check_dict[key_name].tolist() :
        check_nan[key_name] = "N"
        
    try:
        file_upload[key_name].astype(float)
        check_float[key_name] = "Y"
    except:
        check_float[key_name] = "N"
# file_upload["DRPD_BuildingArea"].astype(float)
check_float.values() == check_float_last.values()

file["len"] = file["DRPD_LandUseType"].apply(lambda x : len_str(x))
check = file[["DRPD_LandUseType","len"]]
