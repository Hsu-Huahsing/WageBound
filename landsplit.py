# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 13:21:03 2024

@author: Z00051711
"""

# =============================================================================
# final_price      是用四號公報算出來的沒有經過任何調整
# final_price_adj  把final_price用倍數調整
# final_price_adj2 把final_price用平移調整
# 要先去VDI跑一隻程式，叫透天房地分離，把結果檔攜出，就是ctbc_inside
# =============================================================================


import pandas as pd
from ctbc_project.config import build_cost, ctbc_mainmaterial_ref, ctbc_mainmaterial_ref_temp, cityname_change, seg_price_num
from numpy import NAN, nan
from os.path import join
from datetime import date
today_str = date.today().strftime("%Y%m%d")

def dict_get_value(d={}, val=0):
    for key in d:
        if d[key] == val:
            return key

def buildcost_get(city="", price_mean=0):
    # print(city,price_mean)
    # print(type(city),type(price_mean))
    for key in build_cost[city]:
        if price_mean in build_cost[city][key]:
            return key

def changedate(series=None):
    df = series.str.split("年|月|日", expand=True).rename(columns={0: "year", 1: "month", 2: "day"})
    df.loc[:, 'day'] = '1'
    df.loc[:, "year"] = (pd.to_numeric(df.loc[:, "year"], downcast="integer", errors='coerce') + 1911).apply(lambda x : "{:.0f}".format(x))
    return pd.to_datetime(df.loc[:, ["year","month","day"]], errors="coerce")

def segprice_get(key = [] ,city="", totalfloorflag="", mainmaterialcode="", segflag=""):
    if mainmaterialcode == 2:
        segflag = "seg1_price"
    seg_price = data_buildcost.loc[(data_buildcost["city"]==city) & (data_buildcost["total_floor_flag"]==totalfloorflag) & (data_buildcost["Main_Material_Code"]==mainmaterialcode) ,segflag]
    print(city)
    print(seg_price)
    if seg_price.empty is True:
        return key + [None]
    else:
        return key + [seg_price.iloc[0]]



def num_std(n,std):
    s = round(n/std,0)
    return round(std*s,1)


# num_std(1.666)
# num_std(1.49999)
# =============================================================================
# =============================================================================
# =============================================================================
# 前置作業
path_vartable_pcsm = r"D:\數位專案\透天房地分離\策略系統\Build_Cost_Table.csv"
path_vartable = r"E:\數位專案\HPM2.0\2025-11RC\策略系統參數表彙整_20250528.xlsx"
path_buildindex = r"E:\數位專案\HPM2.0\2025-11RC\建築工程總指數251030.xlsx"
path_ap = r'D:\DGIS\workbench\202510\上傳DGIS\GEOM_CTBC_RealPriceDetail.csv'
path_landsplit = r"E:\數位專案\HPM2.0\2025-11RC"
date = '2025-4-1'

data_var_pcsm = pd.read_csv(path_vartable_pcsm,dtype=str)
data_var = pd.read_excel(path_vartable, sheet_name=None)
data_buildindex = pd.read_excel(path_buildindex, sheet_name="月").rename(columns={"統計期":"apply_date","建築工程總指數":"buildindex"})
data_buildcost_upload = data_var["build_cost_table"].drop_duplicates().rename(columns={"city":"After_five","zip_code":"Area_Nbr"}).astype(str)
data_buildcost = data_var["build_cost_table"].drop(["zip_code","price_level"],axis=1).drop_duplicates()
data_buildcost_zip = data_var["build_cost_table"].drop(["city","total_floor_flag","price_level"],axis=1).drop_duplicates()
data_buildcost_city = data_var["build_cost_table"].drop(["zip_code","total_floor_flag","price_level"],axis=1).drop_duplicates()
data_remaining_durable_table = data_var["remaining_durable_table"].rename(columns={"Main_Material_Code":"Main_Material_Code_ref"})
data_ap = pd.read_csv(path_ap, sep="|", parse_dates=["DRPD_TradeDate", "DRPD_CompletionDate"], keep_date_col=True, low_memory=False, dtype={"DRPD_ZipCode":str})
data_ctbc = pd.read_excel(join(path_landsplit,r"ctbc_inside.xlsx"))

# =============================================================================
# =============================================================================
# =============================================================================

data_ctbc.loc[data_ctbc[["Application_Nbr","Collateral_Nbr"]].duplicated()]
data_buildindex["apply_date"] = changedate(series=data_buildindex["apply_date"])

data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("鋼骨|SRC|S．R．C",regex=True,na=False) ,'Main_Material_Code_temp'] = 1
data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("鋼筋混凝土|RC|R．C",regex=True,na=False) & (data_ap['Main_Material_Code_temp'].isna()) ,'Main_Material_Code_temp']  = 2
data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("加強磚",regex=True,na=False) & (data_ap['Main_Material_Code_temp'].isna()) , 'Main_Material_Code_temp'] = 3
data_ap.loc[data_ap["DRPD_MainMaterial"].str.contains("鋼架",regex=True,na=False) & (data_ap['Main_Material_Code_temp'].isna()) , 'Main_Material_Code_temp'] = 4
data_ap.loc[(data_ap['Main_Material_Code_temp'].isna()),'Main_Material_Code_temp'] = 5
data_ap['Main_Material_Code_temp'].value_counts()

data_ctbc["Main_Material_Code_ref"] = data_ctbc["Main_Material_Code"].map(lambda x :ctbc_mainmaterial_ref[x] if x in ctbc_mainmaterial_ref else x)
data_ctbc["Main_Material_Code_temp"] = data_ctbc["Main_Material_Code_ref"].map(lambda x :ctbc_mainmaterial_ref_temp[x] if x in ctbc_mainmaterial_ref_temp else 2)

data_ctbc["Main_Material_Code_temp"].value_counts()

data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==1) & (data_ap["DRPD_TotalFloorFlag"]<=3) ,"total_floor_flag"]  = "01.<=3"
data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==1) & ((data_ap["DRPD_TotalFloorFlag"]<=5) & (data_ap["total_floor_flag"]=="nan")) , "total_floor_flag"] = "02.<=5"
data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==1) & ((data_ap["DRPD_TotalFloorFlag"]<=8) & (data_ap["total_floor_flag"]=="nan")) , "total_floor_flag"] = "03.<=8"
data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==1) & ((data_ap["DRPD_TotalFloorFlag"]<=10) & (data_ap["total_floor_flag"]=="nan")) , "total_floor_flag"] = "04.<=10"
data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==1) & (data_ap["total_floor_flag"]=="nan"),"total_floor_flag"] = "05.>10"
data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==2) & (data_ap["DRPD_TotalFloorFlag"]<=3) ,"total_floor_flag"]  = "01.<=3"
data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==2) & ((data_ap["DRPD_TotalFloorFlag"]<=5) & (data_ap["total_floor_flag"]=="nan")) , "total_floor_flag"] = "02.<=5"
data_ap.loc[(data_ctbc["Main_Material_Code_temp"]==2) & (data_ap["total_floor_flag"]=="nan"),"total_floor_flag"] = "03.>5"
data_ap["total_floor_flag"].value_counts()

data_ap = data_ap.loc[ ~data_ap["DRPD_MainPurpose"].isin([NAN,"工業用","其他","農業用"]) & data_ap["DRPD_NoteFlag"].isna() & data_ap['DRPD_TransFloorFlag'].between(2,998) ,:] # data_ap['Main_Material_Code_temp'].isin([1, 2]) &

data_ctbc = data_ctbc.replace(cityname_change, regex=True)

data_ctbc.loc[data_ctbc["Total_Floor_Cnt"]<=3 ,"total_floor_flag"]  = "01.<=3"
data_ctbc.loc[(data_ctbc["Total_Floor_Cnt"]<=5) & (data_ctbc["total_floor_flag"]=="nan") , "total_floor_flag"] = "02.<=5"
data_ctbc.loc[(data_ctbc["Total_Floor_Cnt"]<=8) & (data_ctbc["total_floor_flag"]=="nan") , "total_floor_flag"] = "03.<=8"
data_ctbc.loc[(data_ctbc["Total_Floor_Cnt"]<=10) & (data_ctbc["total_floor_flag"]=="nan") , "total_floor_flag"] = "04.<=10"
data_ctbc.loc[(data_ctbc["total_floor_flag"]=="nan"),"total_floor_flag"] = "05.>10"
data_ctbc["total_floor_flag"].value_counts()

data_ctbc.loc[data_ctbc["Building_Age"]<=5 ,"Building_Age_flag"]  = "01.<=5"
data_ctbc.loc[(data_ctbc["Building_Age"]<=10) & (data_ctbc["Building_Age_flag"]=="nan") , "Building_Age_flag"] = "02.5< & <=10"
data_ctbc.loc[(data_ctbc["Building_Age"]<=15) & (data_ctbc["Building_Age_flag"]=="nan") , "Building_Age_flag"] = "03.10< & <=15"
data_ctbc.loc[(data_ctbc["Building_Age"]<=20) & (data_ctbc["Building_Age_flag"]=="nan") , "Building_Age_flag"] = "04.15< & <=20"
data_ctbc.loc[(data_ctbc["Building_Age"]<=25) & (data_ctbc["Building_Age_flag"]=="nan") , "Building_Age_flag"] = "05.20< & <=25"
data_ctbc.loc[(data_ctbc["Building_Age"]<=30) & (data_ctbc["Building_Age_flag"]=="nan") , "Building_Age_flag"] = "06.25< & <=30"
data_ctbc.loc[(data_ctbc["Building_Age"]<=40) & (data_ctbc["Building_Age_flag"]=="nan") , "Building_Age_flag"] = "06.30< & <=40"
data_ctbc.loc[(data_ctbc["Building_Age"]<=50) & (data_ctbc["Building_Age_flag"]=="nan") , "Building_Age_flag"] = "07.40< & <=50"
data_ctbc.loc[(data_ctbc["Building_Age_flag"]=="nan"),"Building_Age_flag"] = "08.>50"
data_ctbc["Building_Age_flag"].value_counts()

data_ctbc.loc[data_ctbc["Building_Age"]<=10 ,"Building_Age_flag2"]  = "01.<=10"
data_ctbc.loc[(data_ctbc["Building_Age"]<=20) & (data_ctbc["Building_Age_flag2"]=="nan") , "Building_Age_flag2"] = "02.10< & <=20"
data_ctbc.loc[(data_ctbc["Building_Age"]<=30) & (data_ctbc["Building_Age_flag2"]=="nan") , "Building_Age_flag2"] = "03.20< & <=30"
data_ctbc.loc[(data_ctbc["Building_Age_flag2"]=="nan"),"Building_Age_flag2"] = "08.>30"
data_ctbc["Building_Age_flag2"].value_counts()

data_ctbc["Date"] = data_ctbc["Application_Nbr"].str.slice(start=0, stop=6)

data_ctbc = data_ctbc.loc[(data_ctbc["total_floor_flag"]!="05.>10") & data_ctbc["Main_Material_Code"].isin([1,2,3,4]) ,:]
# data_ctbc = data_ctbc.loc[(data_ctbc["total_floor_flag"]!="05.>10") ,:]

DateRange_ap = pd.date_range(start=date, periods=2, freq=pd.offsets.MonthBegin(6),inclusive='both')
DateRange_ctbc = pd.date_range(start=date, periods=6, freq='MS').map(lambda x : x.strftime("%Y%m"))

data_ap = data_ap.loc[data_ap["DRPD_TradeDate"].between(DateRange_ap[0], DateRange_ap[1], inclusive="left")]
data_ctbc = data_ctbc.loc[data_ctbc["Date"].isin(DateRange_ctbc)]

# data_ctbc["Main_Material_Code"].value_counts()

pivot1 = data_ap.groupby(["DRPD_City","DRPD_ZipCode"]).agg({'DRPD_UnitPriceRevised':'median','DRPD_Number':'size'}).reset_index().rename(columns={"DRPD_City":"After_five", "DRPD_ZipCode":"Area_Nbr","DRPD_Number":"counts1"})
pivot1_col = pivot1.columns.tolist()+["seg_final"]
pivot1 = [_+[buildcost_get(city=_[0],price_mean=round(_[-2],0))] for _ in pivot1.values.tolist()]
pivot1 = pd.DataFrame(pivot1,columns=pivot1_col)
pivot1["pivot1_nbr"] = 1
pivot1 = pivot1.loc[pivot1["counts1"]>30,:]

pivot2 = data_ap.groupby(["DRPD_City", "total_floor_flag"]).agg({'DRPD_UnitPriceRevised':'median','DRPD_Number':'size'}).reset_index().rename(columns={"DRPD_City":"After_five","DRPD_Number":"counts2"})
pivot2_col = pivot2.columns.tolist()+["seg_final"]
pivot2 = [_+[buildcost_get(city=_[0],price_mean=round(_[-2],0))] for _ in pivot2.values.tolist()]
pivot2 = pd.DataFrame(pivot2,columns=pivot2_col)
pivot2["pivot2_nbr"] = 2
pivot2 = pivot2.loc[pivot2["counts2"]>30,:]

pivot3 = data_ap.groupby(["DRPD_City"]).agg({'DRPD_UnitPriceRevised':'median','DRPD_Number':'size'}).reset_index().rename(columns={"DRPD_City":"After_five","DRPD_Number":"counts3"})
pivot3_col = pivot3.columns.tolist()+["seg_final"]
pivot3 = [_+[buildcost_get(city=_[0],price_mean=round(_[-2],0))] for _ in pivot3.values.tolist()]
pivot3 = pd.DataFrame(pivot3,columns=pivot3_col)
pivot3["pivot3_nbr"] = 3

data_ctbc["Area_Nbr"] = data_ctbc["Area_Nbr"].astype(str)

data_ctbc = pd.merge(data_ctbc, pivot1[["Area_Nbr","seg_final"]].astype(str),on=["Area_Nbr"], how = "left")
data_ctbc = pd.merge(data_ctbc, pivot2[["After_five","total_floor_flag","seg_final"]].astype(str), on=["After_five","total_floor_flag"], how = "left", suffixes=("","_pivot2"))
data_ctbc = pd.merge(data_ctbc, pivot3[["After_five","seg_final"]].astype(str), on=["After_five"], how = "left", suffixes=("","_pivot3"))

data_ctbc.loc[data_ctbc["seg_final"].isna(),"seg_final"] = data_ctbc["seg_final_pivot2"]
data_ctbc.loc[data_ctbc["seg_final"].isna(),"seg_final"] = data_ctbc["seg_final_pivot3"]

data_ctbc.loc[data_ctbc["seg_final"].isna(),:]

data_buildcost_upload = pd.merge(data_buildcost_upload, pivot1[["After_five","Area_Nbr","seg_final",'counts1','pivot1_nbr']], on=["After_five","Area_Nbr"],how="left")
data_buildcost_upload = pd.merge(data_buildcost_upload, pivot2[["After_five","total_floor_flag","seg_final",'counts2','pivot2_nbr']].rename(columns={"seg_final":"seg_final_2"}), on=["After_five","total_floor_flag"],how="left")
data_buildcost_upload = pd.merge(data_buildcost_upload, pivot3[["After_five","seg_final",'counts3','pivot3_nbr']].rename(columns={"seg_final":"seg_final_3"}), on=["After_five"],how="left")

data_buildcost_upload.loc[data_buildcost_upload["seg_final"].isna(),["seg_final","counts1","pivot1_nbr"]] = data_buildcost_upload[["seg_final_2","counts2","pivot2_nbr"]].rename(columns={"seg_final_2":"seg_final","counts2":"counts1","pivot2_nbr":"pivot1_nbr"})
data_buildcost_upload.loc[data_buildcost_upload["seg_final"].isna(),["seg_final","counts1","pivot1_nbr"]] = data_buildcost_upload.loc[:,["seg_final_3","counts3","pivot3_nbr"]].rename(columns={"seg_final_3":"seg_final","counts3":"counts1","pivot3_nbr":"pivot1_nbr"})
data_buildcost_upload = data_buildcost_upload.rename(columns={"seg_final":"Seg_Index"})
data_buildcost_upload["Build_Cost_Key"] = data_buildcost_upload["Area_Nbr"] +"_"+ data_buildcost_upload["total_floor_flag"].str.slice(0,2) +"_"+ data_buildcost_upload["Main_Material_Code"].str.zfill(2)
# data_buildcost_upload = data_buildcost_upload.drop(columns=["Area_Nbr","After_five","total_floor_flag","Main_Material_Code","seg_final_2","seg_final_3","price_level"])

with pd.ExcelWriter(r"E:\數位專案\HPM2.0\2025-11RC\Build_Cost_Table_{}.xlsx".format(today_str)) as writer :
    data_buildcost_upload.to_excel(writer, sheet_name='check', index=False, engine='xlsxwriter')
    data_buildcost_upload = data_buildcost_upload.reindex(columns=["Build_Cost_Key","segprice1","segprice2","segprice3","segprice4","segprice5","segprice6","segprice7","segprice8","segprice9","Index"])
    data_buildcost_upload["Index"] = data_buildcost_upload["Index"].apply(lambda x : seg_price_num[x] if x in seg_price_num else 1)
    data_buildcost_upload.to_excel(writer, sheet_name='upload', index=False, engine='xlsxwriter')

# data_buildcost_upload = data_buildcost_upload.reindex(columns=["Build_Cost_Key","seg1_price","seg2_price","seg3_price","seg4_price","seg5_price","seg6_price","seg7_price","seg8_price","seg9_price","Seg_Index"])
# data_buildcost_upload["Seg_Index"] = data_buildcost_upload["Seg_Index"].apply(lambda x : seg_price_num[x] if x in seg_price_num else 1)
# data_buildcost_upload.to_csv(r"D:\數位專案\透天房地分離\Build_Cost_Table_{}.csv".format(today_str),index=False, encoding = 'utf8')

data_ctbc_temp = [ segprice_get(key=[_[0],_[1]], city=_[2], totalfloorflag=_[3], mainmaterialcode=_[4], segflag=_[5]) for _ in data_ctbc[["Application_Nbr","Collateral_Nbr","After_five","total_floor_flag",'Main_Material_Code_temp',"seg_final"]].values]
data_ctbc_temp = pd.DataFrame(data_ctbc_temp,columns=["Application_Nbr","Collateral_Nbr","segfinal_price"])

data_ctbc["apply_date"] = data_ctbc["Aprl_Date"].map(lambda x : pd.to_datetime("{}-{}-01".format(x.year,x.month)))
data_ctbc = pd.merge(data_ctbc, data_buildindex, on=["apply_date"], how="left")

data_ctbc = pd.merge(data_ctbc, data_ctbc_temp, on=["Application_Nbr","Collateral_Nbr"], how="left" )
data_ctbc = pd.merge(data_ctbc, data_remaining_durable_table[["Main_Material_Code_ref","remaining_rate","durable_year"]], on=["Main_Material_Code_ref"], how="left")

data_ctbc.loc[data_ctbc["Main_Material_Code"].isin([3,4]),"segfinal_price"] = data_ctbc["segfinal_price"]+37500
data_ctbc["buildindex"] = data_ctbc["buildindex"]/100
data_ctbc["remaining_year"] = data_ctbc["durable_year"]-data_ctbc["Building_Age"]
data_ctbc["segfinal_price"] = data_ctbc["segfinal_price"]/10000
data_ctbc["segfinal_price"] = data_ctbc["segfinal_price"]*data_ctbc["buildindex"]
data_ctbc.loc[data_ctbc["remaining_year"]<=0,"final_price"] = data_ctbc["segfinal_price"]*data_ctbc["remaining_rate"]
data_ctbc.loc[(data_ctbc["remaining_year"]> 0),"final_price"] = data_ctbc["segfinal_price"]-(data_ctbc["Building_Age"]/data_ctbc["durable_year"]*(1-data_ctbc["remaining_rate"]))*data_ctbc["segfinal_price"]

# a=data_ctbc.loc[data_ctbc["final_price"].isna(),:]

data_ctbc["final_price_diff"] = data_ctbc["final_price"]-data_ctbc["BuildPrice"]

data_ctbc["Build_MAPE"] = data_ctbc["final_price_diff"]/data_ctbc["BuildPrice"]
data_ctbc["Build_MAPE_abs"] = abs(data_ctbc["final_price_diff"]/data_ctbc["BuildPrice"])

table_var1 = data_ctbc.groupby(["Area_Nbr","total_floor_flag","Building_Age_flag2"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index() #.rename(columns={"DRPD_City":"After_five"})
table_var1["Var"] = table_var1["BuildPrice"]/table_var1["final_price"]
table_var1["Var2"] = table_var1["BuildPrice"]-table_var1["final_price"]
table_var1 = table_var1.loc[table_var1["Application_Nbr"]>30,:]

table_var2 = data_ctbc.groupby(["Area_Nbr","Building_Age_flag2"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index() #.rename(columns={"DRPD_City":"After_five"})
table_var2["Var"] = table_var2["BuildPrice"]/table_var2["final_price"]
table_var2["Var2"] = table_var2["BuildPrice"]-table_var2["final_price"]
table_var2 = table_var2.loc[table_var2["Application_Nbr"]>30,:]

table_var3 = data_ctbc.groupby(["Area_Nbr"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index() #.rename(columns={"DRPD_City":"After_five"})
table_var3["Var"] = table_var3["BuildPrice"]/table_var3["final_price"]
table_var3["Var2"] = table_var3["BuildPrice"]-table_var3["final_price"]
table_var3 = table_var3.loc[table_var3["Application_Nbr"]>30,:]

table_var4 = data_ctbc.groupby(["County"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index() #.rename(columns={"DRPD_City":"After_five"})
table_var4["Var"] = table_var4["BuildPrice"]/table_var4["final_price"]
table_var4["Var2"] = table_var4["BuildPrice"]-table_var4["final_price"]
# table_var4 = table_var4.loc[table_var4["Application_Nbr"]>30,:]

data_ctbc = pd.merge(data_ctbc,table_var1[["Area_Nbr","total_floor_flag","Building_Age_flag2","Var","Var2"]], on=["Area_Nbr","total_floor_flag","Building_Age_flag2"], how="left" )
data_ctbc = pd.merge(data_ctbc,table_var2[["Area_Nbr","Building_Age_flag2","Var","Var2"]], on=["Area_Nbr","Building_Age_flag2"], how="left" , suffixes=("","_2"))
data_ctbc = pd.merge(data_ctbc,table_var3[["Area_Nbr","Var","Var2"]].astype(str), on=["Area_Nbr"], how = "left", suffixes=("","_3"))
data_ctbc = pd.merge(data_ctbc,table_var4[["County","Var","Var2"]].astype(str), on=["County"], how = "left", suffixes=("","_4"))

data_ctbc["Level"] = "1"
data_ctbc["Level2"] = "1"
data_ctbc.loc[data_ctbc["Var"].isna(),"Level"] = "2"
data_ctbc.loc[data_ctbc["Var2"].isna(),"Level2"] = "2"
data_ctbc.loc[data_ctbc["Var"].isna(),"Var"] = data_ctbc["Var_2"]
data_ctbc.loc[data_ctbc["Var2"].isna(),"Var2"] = data_ctbc["Var2_2"]
data_ctbc.loc[data_ctbc["Var"].isna(),"Level"] = "3"
data_ctbc.loc[data_ctbc["Var2"].isna(),"Level2"] = "3"
data_ctbc.loc[data_ctbc["Var"].isna(),"Var"] = data_ctbc["Var_3"]
data_ctbc.loc[data_ctbc["Var2"].isna(),"Var2"] = data_ctbc["Var2_3"]
data_ctbc.loc[data_ctbc["Var"].isna(),"Level"] = "4"
data_ctbc.loc[data_ctbc["Var2"].isna(),"Level2"] = "4"
data_ctbc.loc[data_ctbc["Var"].isna(),"Var"] = data_ctbc["Var_4"]
data_ctbc.loc[data_ctbc["Var2"].isna(),"Var2"] = data_ctbc["Var2_4"]

data_ctbc.loc[data_ctbc["Var"].isna(),:]
data_ctbc["Var"] = data_ctbc["Var"].astype(float)
data_ctbc["Var"] = data_ctbc["Var"].map(lambda x : num_std(x,0.2))

data_ctbc.loc[data_ctbc["Var2"].isna(),:]
data_ctbc["Var2"] = data_ctbc["Var2"].astype(float)
data_ctbc["Var2"] = data_ctbc["Var2"].map(lambda x : num_std(x,0.5))

data_ctbc.loc[data_ctbc["remaining_year"]>0 ,"final_price_adj"] = data_ctbc["final_price"]*data_ctbc["Var"]
data_ctbc.loc[data_ctbc["remaining_year"]<=0 ,"final_price_adj"] = data_ctbc["final_price"]

data_ctbc.loc[data_ctbc["remaining_year"]>0 ,"final_price_adj2"] = data_ctbc["final_price"]+data_ctbc["Var2"]
data_ctbc.loc[data_ctbc["remaining_year"]<=0 ,"final_price_adj2"] = data_ctbc["final_price"]

data_ctbc.loc[(data_ctbc["remaining_year"]>0) & (data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) & (data_ctbc["final_price_adj2"]<3) ,"final_price_adj2"] = 3
data_ctbc.loc[(data_ctbc["remaining_year"].between(-3,0)) & (data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) & (data_ctbc["final_price_adj2"]<3) ,"final_price_adj2"] = 3
data_ctbc.loc[(data_ctbc["remaining_year"].between(-9,-4)) & (data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) & (data_ctbc["final_price_adj2"]<2.5),"final_price_adj2"] = 2.5
data_ctbc.loc[(data_ctbc["remaining_year"]<=-10) & data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"]) & (data_ctbc["final_price_adj2"]<1.5),"final_price_adj2"] = 1.5
data_ctbc.loc[(data_ctbc["remaining_year"]>0) & (~data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) & (data_ctbc["final_price_adj2"]<1),"final_price_adj2"] = 1
data_ctbc.loc[(data_ctbc["remaining_year"].between(-3,0)) & (~data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) & (data_ctbc["final_price_adj2"]<1),"final_price_adj2"] = 1
data_ctbc.loc[(data_ctbc["remaining_year"].between(-9,-4)) & (~data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) & (data_ctbc["final_price_adj2"]<0.8),"final_price_adj2"] = 0.8
data_ctbc.loc[(data_ctbc["remaining_year"]<=-10) & (~data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) & (data_ctbc["final_price_adj2"]<0.5),"final_price_adj2"] = 0.5
# data_ctbc.loc[data_ctbc["final_price"] < 0.5,"final_price"] = 0.5
# data_ctbc.loc[(data_ctbc["remaining_year"].between(-3,0)) & (~data_ctbc["After_five"].isin(["台中市","南投縣","彰化縣"])) ,"final_price"]

data_ctbc["final_price_adj2_diff"] = data_ctbc["final_price_adj2"]-data_ctbc["BuildPrice"]
data_ctbc["final_price_adj_diff"] = data_ctbc["final_price_adj"]-data_ctbc["BuildPrice"]
data_ctbc["final_price_diff"] = data_ctbc["final_price"]-data_ctbc["BuildPrice"]
data_ctbc["adj_diff"] = abs(data_ctbc["final_price_adj"]-data_ctbc["final_price"])

# data_ctbc.loc[data_ctbc["remaining_year"]>0 ,"final_price_adj_range"] = data_ctbc["final_price"]*abs(data_ctbc["Var"]-1)
# data_ctbc.loc[data_ctbc["remaining_year"]<=0 ,"final_price_adj_range"] = 0.5


# d = data_ctbc.loc[data_ctbc["Application_Nbr"]=="20230310EI00032",:]

# data_ctbc.loc[(data_ctbc["remaining_year"]>0) & ((data_ctbc["adj_diff"]>0) & (round(data_ctbc["adj_diff"],4) <= round(data_ctbc["final_price_adj_range"],4)) | ((data_ctbc["Var"]==1)&(data_ctbc["adj_diff"]==0)) ),"final_price_adj_OK"] = "Y"
# data_ctbc.loc[(data_ctbc["remaining_year"]<=0) & (data_ctbc["final_price_adj"]==0.5) & (data_ctbc["final_price_adj_OK"]=="n") ,"final_price_adj_OK"] = "Y"
# data_ctbc.loc[data_ctbc["final_price_adj_OK"]=="nan" ,"final_price_adj_OK"] = "N"

# b = data_ctbc.loc[data_ctbc["final_price_adj_OK"]!="Y" , :]

data_ctbc["Build_MAPE_adj"] = data_ctbc["final_price_adj_diff"]/data_ctbc["BuildPrice"]
data_ctbc["Build_MAPE_abs_adj"] = abs(data_ctbc["final_price_adj_diff"]/data_ctbc["BuildPrice"])
data_ctbc["Build_MAPE"] = data_ctbc["final_price_diff"]/data_ctbc["BuildPrice"]

check3 = data_ctbc.groupby(["After_five", "total_floor_flag"])["Build_MAPE_abs_adj"].mean().reset_index()

data_ctbc.loc[data_ctbc["final_price_diff"]<=-4 ,"diff_flag"]  = "01.<=-4"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=-2) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "02.-4< & <=-2"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=-1) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "03.-2< & <=-1"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=-0.5) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "04.-1< & <=-0.5"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=0) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "05.-0.5< & <=0"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=0.5) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "06.0< & <=0.5"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=1) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "07.0.5< & <=1"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=2) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "08.1< & <=2"
data_ctbc.loc[(data_ctbc["final_price_diff"]<=4) & (data_ctbc["diff_flag"]=="nan") , "diff_flag"] = "09.2< & <=4"
data_ctbc.loc[(data_ctbc["diff_flag"]=="nan"),"diff_flag"] = "10.>4"
data_ctbc["diff_flag"].value_counts()

data_ctbc.loc[data_ctbc["final_price_adj_diff"]<=-4 ,"adj_diff_flag"]  = "01.<=-4"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=-2) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "02.-4< & <=-2"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=-1) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "03.-2< & <=-1"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=-0.5) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "04.-1< & <=-0.5"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=0) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "05.-0.5< & <=0"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=0.5) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "06.0< & <=0.5"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=1) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "07.0.5< & <=1"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=2) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "08.1< & <=2"
data_ctbc.loc[(data_ctbc["final_price_adj_diff"]<=4) & (data_ctbc["adj_diff_flag"]=="nan") , "adj_diff_flag"] = "09.2< & <=4"
data_ctbc.loc[(data_ctbc["adj_diff_flag"]=="nan"),"adj_diff_flag"] = "10.>4"
data_ctbc["adj_diff_flag"].value_counts()

data_ctbc.loc[data_ctbc["final_price_adj2_diff"]<=-4 ,"adj2_diff_flag"]  = "01.<=-4"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=-2) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "02.-4< & <=-2"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=-1) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "03.-2< & <=-1"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=-0.5) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "04.-1< & <=-0.5"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=0) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "05.-0.5< & <=0"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=0.5) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "06.0< & <=0.5"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=1) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "07.0.5< & <=1"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=2) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "08.1< & <=2"
data_ctbc.loc[(data_ctbc["final_price_adj2_diff"]<=4) & (data_ctbc["adj2_diff_flag"]=="nan") , "adj2_diff_flag"] = "09.2< & <=4"
data_ctbc.loc[(data_ctbc["adj2_diff_flag"]=="nan"),"adj2_diff_flag"] = "10.>4"
data_ctbc["adj2_diff_flag"].value_counts()
# e = data_ctbc["Var"].value_counts()
table_var4 = data_ctbc.groupby(["County"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index() #.rename(columns={"DRPD_City":"After_five"})

check1 = data_ctbc.loc[data_ctbc["remaining_year"]>0,:].groupby(["After_five"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index()
check2 = data_ctbc.loc[data_ctbc["remaining_year"]>0,:].groupby(["After_five","Building_Age_flag2"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index().sort_values(by="Building_Age_flag2")
check3 = data_ctbc.loc[data_ctbc["remaining_year"]>0,:].groupby(["Building_Age_flag2"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index().sort_values(by="Building_Age_flag2")
check4 = data_ctbc.loc[data_ctbc["remaining_year"]>0,:].agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index()
check5 = data_ctbc.loc[data_ctbc["remaining_year"]<=0,:].groupby(["After_five"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index()
check6 = data_ctbc.loc[data_ctbc["remaining_year"]<=0,:].agg({'Application_Nbr':'size','BuildPrice':'median','final_price':'median'}).reset_index()

check7 = data_ctbc.loc[(data_ctbc["After_five"]=="台中市") & (data_ctbc["remaining_year"]>0),["Application_Nbr","Building_Age","BuildPrice","final_price","final_price_adj2"]]
check8 = data_ctbc.loc[(data_ctbc["After_five"]=="南投縣") & (data_ctbc["remaining_year"]>0),["Application_Nbr","Building_Age","BuildPrice","final_price","final_price_adj2"]]
check9 = data_ctbc.loc[(data_ctbc["After_five"]=="彰化縣") & (data_ctbc["remaining_year"]>0),["Application_Nbr","Building_Age","BuildPrice","final_price","final_price_adj2"]]

check10 = data_ctbc.loc[data_ctbc["remaining_year"]<=0,:].groupby(["After_five"]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price_adj2':'median'}).reset_index()

# a = data_ctbc.loc[(data_ctbc["After_five"]=="台中市") & (data_ctbc["remaining_year"]>0),["Application_Nbr","Building_Age","BuildPrice","final_price","final_price_adj"]]
e = data_ctbc.loc[ (data_ctbc["remaining_year"]>0),["After_five","Application_Nbr","Building_Age_flag2","BuildPrice","final_price","final_price_adj2"]]
# (data_ctbc["County"]=="台中市") &
e = e.groupby(["After_five" ]).agg({'Application_Nbr':'size','BuildPrice':'median','final_price_adj2':'median'}).reset_index()
# , "Building_Age_flag2"


b = data_ctbc.loc[data_ctbc["Application_Nbr"].isin(["20230224EI00159"]),:]
c = data_ctbc.loc[data_ctbc["Area_Nbr"].isin(["320"]) & data_ctbc["total_floor_flag"].isin(["01.<=3"]) & data_ctbc["Building_Age_flag"].isin(["07.40< & <=50"]),:]


# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================
# 資料驗證

path_ITcheck = r"D:\數位專案\2024_12RC\驗證用"
data_ITcheck = pd.read_excel(join(path_ITcheck,r"LOG_PCSM_uat.xlsx"), sheet_name=None)
data_ITcheck_input = data_ITcheck["pcsm_input"]
data_ITcheck_output = data_ITcheck["pcsm_output"]
data_temp5 = pd.read_csv(join(path_landsplit,r"Build_Cost_Table.csv"), dtype=str)

from datetime import date
def segprice_get(key=""):
    seg = data_var_pcsm.loc[data_var_pcsm["Build_Cost_Key"]==key,:]
    # print(seg)
    # print(key)
    seg_flag = dict_get_value(d=seg_price_num, val=int(seg["Seg_Index"].values[0]))
    return seg[seg_flag].values[0]
    
sysdate = date.today()
temp1 = pd.merge(data_ITcheck_input.rename(columns={"CollateralNbr":"CollateralNo"}), data_ITcheck_output,on=["applno","CollateralNo"],how="left")
temp1 = temp1.loc[temp1["BuildingType"].isin(["R4","R5"])&(temp1["HpmModelFlag"]=="Y")&(temp1["HierachyFlag"]=="2")& (temp1["RRefUnitPrice"]==0),:]

temp1["Main_Material_Code_ref"] = temp1["MainMaterialCode"].map(lambda x :ctbc_mainmaterial_ref[x] if x in ctbc_mainmaterial_ref else x)
temp1["Main_Material_Code_temp"] = temp1["Main_Material_Code_ref"].map(lambda x :ctbc_mainmaterial_ref_temp[x] if x in ctbc_mainmaterial_ref_temp else x)

temp1.loc[(temp1["Main_Material_Code_temp"]==1) & (temp1["TotalFloor"]<=3) ,"total_floor_flag"]  = "01"
temp1.loc[(temp1["Main_Material_Code_temp"]==1) & ((temp1["TotalFloor"]<=5) & (temp1["total_floor_flag"]=="na")) , "total_floor_flag"] = "02"
temp1.loc[(temp1["Main_Material_Code_temp"]==1) & ((temp1["TotalFloor"]<=8) & (temp1["total_floor_flag"]=="na")) , "total_floor_flag"] = "03"
temp1.loc[(temp1["Main_Material_Code_temp"]==1) & ((temp1["TotalFloor"]<=10) & (temp1["total_floor_flag"]=="na")) , "total_floor_flag"] = "04"
temp1.loc[(temp1["Main_Material_Code_temp"]==1) & (temp1["total_floor_flag"]=="na"),"total_floor_flag"] = "05"
temp1.loc[(temp1["Main_Material_Code_temp"]==2) & (temp1["TotalFloor"]<=3) ,"total_floor_flag"]  = "01"
temp1.loc[(temp1["Main_Material_Code_temp"]==2) & ((temp1["TotalFloor"]<=5) & (temp1["total_floor_flag"]=="na")) , "total_floor_flag"] = "02"
temp1.loc[(temp1["Main_Material_Code_temp"]==2) & (temp1["total_floor_flag"]=="na"),"total_floor_flag"] = "03"
temp1["total_floor_flag"].value_counts()

temp1["Main_Material_Code_temp"] = temp1["Main_Material_Code_temp"].astype(str)

temp1 = pd.merge(temp1, data_remaining_durable_table[["Main_Material_Code_ref","remaining_rate","durable_year"]], on=["Main_Material_Code_ref"], how="left")
temp1.loc[temp1["remaining_rate"]==0.045,"remaining_rate"] = 0.05
temp1["Temp5Key"] = temp1['ZipCode'].astype(str) +"_"+temp1['total_floor_flag']+"_"+temp1["Main_Material_Code_temp"].str.zfill(2)
temp1["seg_price"] = temp1["Temp5Key"].map(lambda x : segprice_get(key=x))
temp1 = temp1.loc[temp1["seg_price"]!="-9,999",:]
temp1 = temp1.replace({"seg_price":{",":""}},regex=True)
if sysdate < date(2024,10,1) :
    temp1["BuildIndex"] = 1.0731
else :
    temp1["BuildIndex"] = 1.0815

temp1["RemainingYear"] = temp1["BuildingAge"] - temp1["durable_year"]
temp1["BuildUnitPolicyPrice_Index"] = temp1["seg_price"].astype(int)*temp1["BuildIndex"]
temp1["Discount"] = temp1["BuildingAge"]*((temp1["BuildUnitPolicyPrice_Index"]-temp1["BuildUnitPolicyPrice_Index"]*temp1["remaining_rate"])/temp1["durable_year"])
temp1["BuildUnitPolicyPrice_before"] = (temp1["BuildUnitPolicyPrice_Index"] - temp1["Discount"]).astype(int)/10000
temp1["BuildUnitPolicyPrice"] = temp1["BuildUnitPolicyPrice_before"]
temp2 = temp1.loc[temp1["ZipCode"].isin([400,401,402,403,404,406,407,408,411,412,413,414,420,421,422,423,424,426,427,428,429,432,433,434,435,436,437,438,439]),:]
temp3 = temp1.loc[temp1["ZipCode"].isin([500,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,520,521,522,523,524,525,526,527,528,530]),:]
temp4 = temp1.loc[temp1["ZipCode"].isin([540,541,542,544,545,546,551,552,553,555,556,557,558]),:]

if temp2.empty is False:
    temp2.loc[(temp2["BuildingAge"]<=10),"BuildUnitPolicyPrice"] = temp2.loc[temp2["BuildingAge"]<=10,"BuildUnitPolicyPrice"]+4
    temp2.loc[(temp2["BuildingAge"]<=20)&(temp2["BuildingAge"]>10),"BuildUnitPolicyPrice"] = temp2.loc[(temp2["BuildingAge"]<=20)&(temp2["BuildingAge"]>10),"BuildUnitPolicyPrice"]+3
    temp2.loc[(temp2["BuildingAge"]<=30)&(temp2["BuildingAge"]>20),"BuildUnitPolicyPrice"] = temp2.loc[(temp2["BuildingAge"]<=30)&(temp2["BuildingAge"]>20),"BuildUnitPolicyPrice"]+2
    temp2.loc[(temp2["BuildingAge"]>30),"BuildUnitPolicyPrice"] = temp2.loc[(temp2["BuildingAge"]>30),"BuildUnitPolicyPrice"]+2
    
if temp3.empty is False:
    temp3.loc[(temp3["BuildingAge"]<=10),"BuildUnitPolicyPrice"] = temp3.loc[temp3["BuildingAge"]<=10,"BuildUnitPolicyPrice"]+3
    temp3.loc[(temp3["BuildingAge"]<=20)&(temp3["BuildingAge"]>10),"BuildUnitPolicyPrice"] = temp3.loc[(temp3["BuildingAge"]<=20)&(temp3["BuildingAge"]>10),"BuildUnitPolicyPrice"]+2
    temp3.loc[(temp3["BuildingAge"]<=30)&(temp3["BuildingAge"]>20),"BuildUnitPolicyPrice"] = temp3.loc[(temp3["BuildingAge"]<=30)&(temp3["BuildingAge"]>20),"BuildUnitPolicyPrice"]+2
    temp3.loc[(temp3["BuildingAge"]>30),"BuildUnitPolicyPrice"] = temp3.loc[(temp3["BuildingAge"]>30),"BuildUnitPolicyPrice"]+2
if temp4.empty is False:
    temp4.loc[(temp4["BuildingAge"]<=10),"BuildUnitPolicyPrice"] = temp4.loc[temp4["BuildingAge"]<=10,"BuildUnitPolicyPrice"]+3
    temp4.loc[(temp4["BuildingAge"]<=20)&(temp4["BuildingAge"]>10),"BuildUnitPolicyPrice"] = temp4.loc[(temp4["BuildingAge"]<=20)&(temp4["BuildingAge"]>10),"BuildUnitPolicyPrice"]+2
    temp4.loc[(temp4["BuildingAge"]<=30)&(temp4["BuildingAge"]>20),"BuildUnitPolicyPrice"] = temp4.loc[(temp4["BuildingAge"]<=30)&(temp4["BuildingAge"]>20),"BuildUnitPolicyPrice"]+2
    temp4.loc[(temp4["BuildingAge"]>30),"BuildUnitPolicyPrice"] = temp4.loc[(temp4["BuildingAge"]>30),"BuildUnitPolicyPrice"]+3
    
temp_spec = pd.concat([temp2,temp3,temp4])

temp_spec.loc[(temp_spec["RemainingYear"]<=0)&(temp_spec["BuildUnitPolicyPrice"]<3),"BuildUnitPolicyPrice"] = 3
temp_spec.loc[((temp_spec["RemainingYear"]>0)&(temp_spec["RemainingYear"]<=3))&temp_spec["MainMaterialCode"].isin([1,2,3,4,10,11,12,18]),"BuildUnitPolicyPrice"] = 3
temp_spec.loc[((temp_spec["RemainingYear"]>0)&(temp_spec["RemainingYear"]<=3))&~temp_spec["MainMaterialCode"].isin([1,2,3,4,10,11,12,18]),"BuildUnitPolicyPrice"] = 1
temp_spec.loc[((temp_spec["RemainingYear"]>3)&(temp_spec["RemainingYear"]<=9))&temp_spec["MainMaterialCode"].isin([1,2,3,4,10,11,12,18]),"BuildUnitPolicyPrice"] = 2.5
temp_spec.loc[((temp_spec["RemainingYear"]>3)&(temp_spec["RemainingYear"]<=9))&~temp_spec["MainMaterialCode"].isin([1,2,3,4,10,11,12,18]),"BuildUnitPolicyPrice"] = 0.8
temp_spec.loc[(temp_spec["RemainingYear"]>=10)&temp_spec["MainMaterialCode"].isin([1,2,3,4,10,11,12,18]),"BuildUnitPolicyPrice"] = 1.5
temp_spec.loc[(temp_spec["RemainingYear"]>=10)&~temp_spec["MainMaterialCode"].isin([1,2,3,4,10,11,12,18]),"BuildUnitPolicyPrice"] = 0.5

temp1 = temp1.loc[~temp1["applno"].isin(temp_spec["applno"].tolist()),:]

temp1.loc[(temp1["RemainingYear"]<=0)&(temp1["BuildUnitPolicyPrice"]<1),"BuildUnitPolicyPrice"] = 1
temp1.loc[(temp1["RemainingYear"]>0)&(temp1["RemainingYear"]<=3),"BuildUnitPolicyPrice"] = 1
temp1.loc[(temp1["RemainingYear"]>3)&(temp1["RemainingYear"]<=9),"BuildUnitPolicyPrice"] = 0.8
temp1.loc[(temp1["RemainingYear"]>=10),"BuildUnitPolicyPrice"] = 0.5

temp = pd.concat([temp_spec,temp1])
temp.to_csv(r"C:\Users\z00188600\Desktop\temp.csv",encoding="utf_8_sig")



# =======================================================================================
# =======================================================================================
# =======================================================================================
# =======================================================================================
# 價格驗證用
ap_check = data_ap.loc[data_ap["DRPD_TradeDate"].between("2023-12-1", "2024-5-1", inclusive="left")]
ap_check = ap_check.loc[ap_check["DRPD_ZipCode"].isin(["203"]),:]
