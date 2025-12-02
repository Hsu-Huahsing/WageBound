# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 16:56:27 2023

@author: Z00051711
"""
from ctbc_project.config import cityname, colname, dropcol, dgiskey_lis, dgiskey
from StevenTricks.fileop import PathWalk_df, picklesave, pickleload

# from StevenTricks.snt import strtodate
from ctbc_project.StevenTricks.snt import strtodate

from copy import deepcopy
import pandas as pd
import datetime 
from numpy import NAN
from os.path import join
from os import makedirs

td = datetime.date.today()

d = pd.date_range(start="2021-4", periods=38, freq="MS")  #要+一個月
d1 = max(d).strftime("%Y-%m-%d") 
d2 = min(d).strftime("%Y-%m-%d") 

path = r'D:\DGIS\原始資料\{}'.format(max(d).strftime("%Y%m") )
wb = r'D:\DGIS\workbench\{}'.format(max(d).strftime("%Y%m") )
wb_processing = r'D:\DGIS\workbench\{}\processing'.format(max(d).strftime("%Y%m") )

makedirs(path, exist_ok=True) , makedirs(wb, exist_ok=True), makedirs(wb_processing, exist_ok=True)

fileTotal = r'GEOM_CTBC_RealPriceDetail.csv'
fileBD = r'building_{}_{}_v.xlsx'.format(d[33].strftime("%Y%m")[2:],d1.replace("-","")[2:6])
fileXY = r"GEOM_CTBC_RealPriceDetail_XY.csv"
fileFishid = r"GEOM_CTBC_RealPriceDetail_fishid.csv"
fileSend = r"GEOM_CTBC_RealPriceDetail_send.csv"

ExcelPath = PathWalk_df(path, fileinclude=['.xls'],level=0)
ExcelPath = ExcelPath.loc[ExcelPath['level']==0,:]
res={}
# 以上前置作業
# ==============================================================================

for FilePath in ExcelPath['path'] :
    file = pd.read_excel(FilePath, None)
    # 實價登錄一個file裡面會包含建物、停車位、不動產租賃、土地
    for vol in cityname:
        if 'list_' + vol.lower() in FilePath :
            city = cityname[vol]
            break
    # 先決定好目前位於哪個city
    for key in file:
        # 開始進行dictionary裡面4個檔案個別的清理
        newkey = key.split('_')[0]
        # key值有可能是XXXX_50000所以要把這種可能性刪除掉
        if newkey not in ["建物","不動產買賣"]:
            continue
        file[key] = file[key].drop(['Unnamed: 35','Unnamed: 0'],axis=1,errors='ignore')
        # 所有檔案都要進行的column drop
        if newkey in colname:
            # 只要有掉進colname就是需要重新rename
            file[key] = file[key].rename(columns=colname[newkey])
        if newkey in dropcol:
            # 只要有掉進dropcol就是需要重新drop col
            file[key] = file[key].drop(columns=dropcol[newkey],errors='ignore')
            
        if file[key].empty is False:
            file[key].insert(0 ,'City',city)
            
            if newkey =='建物':
                temp = file[key]['Building_Completion_Date'].str.split("年|月|日", expand=True).rename(columns={0: "year", 1: "month", 2: "day"})
                temp['year'] = temp['year'].str.zfill(3)
                temp['month'] = temp['month'].str.zfill(2)
                temp['day'] = temp['day'].str.zfill(2)
                file[key]['Building_Completion_Date_v'] = temp['year']+temp['month']+temp['day']

        if newkey not in res:
            res[newkey] = file[key]
        else:
            res[newkey] = pd.concat([res[newkey], file[key]])

picklesave(res["不動產買賣"], join(wb, 'realestate_original') )

real_estate_3m = deepcopy(res["不動產買賣"].loc[res["不動產買賣"]["Trading_Date"]>=date_3m,:])

building_3m = deepcopy(res["建物"].loc[res["建物"]["Number"].isin(real_estate_3m["Number"].values.tolist()),:])

with pd.ExcelWriter(join(wb,fileBD)) as writer :
    building_3m.to_excel(writer, sheet_name='building', index=False, engine='xlsxwriter')

# with pd.ExcelWriter(join(pathfirst, fileRE)) as writer :
#     real_estate_3m.to_excel(writer, sheet_name='Real_Estate', index=False, engine='xlsxwriter')
    
# res["不動產買賣"] = res["不動產買賣"].loc[res["不動產買賣"]["Trading_Date"]>date_3y,:]

data = deepcopy(res["不動產買賣"])
del res, real_estate_3m, building_3m

# data = pickleload(join(wb, 'realestate_original'))

# dgis_df = [dgis_api(a, b) for a,b in data[["Address","Number"]].values ]
# dgis_df = pd.DataFrame(dgis_df).rename(columns={0:"Number",1:"FishID"})#1:"DRPD_TargetX",2:"DRPD_TargetY",3:"FishID"})

# dgis_df.loc[dgis_df["Number"]=="RPUNMLRLIIIGFAO09DA"]
# data.loc[:,['DRPD_TargetX','DRPD_TargetY']] = dgis_df[['DRPD_TargetX','DRPD_TargetY']]

# data = data.merge(dgis_df[["Number","FishID"]], on="Number", how = "left")

# a.loc[:,"length"] = a["Address"].apply(lambda x : len(str(x)))
# b=a['length'].value_counts()
# c= a.loc[a['length']>=100,:]
# c = c.loc[c["Trading_Target"]!="車位"]

data.loc[:,['Trading_Date','Completion_Date']] = data[['Trading_Date','Completion_Date']].applymap(lambda x : strtodate(x))

picklesave(data, join(wb, 'realestate_date') )

data.to_csv(join(wb,fileTotal), sep="|", index = False, encoding = 'utf8')

data = data.loc[data["Trading_Target"] != "土地" , :]
data = data.loc[~data['Building_Type'].isin(["工廠","倉庫","農舍"]),:]

data = data.loc[~data['Completion_Date'].isna(),:]

data.loc[:,"Trading_Date"] = pd.to_datetime(data['Trading_Date'])


data = data.loc[data['Trading_Date'].between(min(d) , max(d),inclusive='both'),:]

data.loc[:,"Address"] = data["Address"].str.slice(stop=30)

data = data.loc[~data["Address"].isna(),:]

data.loc[data['Partition_YN']=='有', 'DRPD_Partition'] = 'Y'
data.loc[data['DRPD_Partition']!='Y', 'DRPD_Partition'] = 'N'
data['DRPD_Partition'].value_counts(dropna=False)

data.loc[data['Management_YN']=='有', 'DRPD_Management'] = 'Y'
data.loc[data['DRPD_Management']!='Y', 'DRPD_Management'] = 'N'
data['DRPD_Management'].value_counts(dropna=False)

# data = data.replace({'Note':{pd.NA:""}}, regex=True)
data.loc[data['Note'].isna(), 'DRPD_HasNote'] = 'N'
data.loc[data['DRPD_HasNote']!='N', 'DRPD_HasNote'] = 'Y'
data['DRPD_HasNote'].value_counts(dropna=False)

data.loc[:, 'DRPD_BuildingAge'] = pd.to_datetime(data['Trading_Date']).dt.year -pd.to_datetime(data['Completion_Date'], errors="coerce", infer_datetime_format=True).dt.year
data.loc[data['DRPD_BuildingAge']<0 , 'DRPD_BuildingAge'] = 0
data.loc[(data['DRPD_BuildingAge']=="nan") , 'DRPD_BuildingAge'] = 10000
data['DRPD_BuildingAge'].value_counts(dropna=False)

data.loc[:,'Land_Trans_Area'] = round(data['Land_Trans_Area']*0.3025,2)
data.loc[:,'Trans_Area'] = round(data['Trans_Area']*0.3025,2)
data.loc[:,'Total_Price'] = round(data['Total_Price']/10000,4)
data.loc[:,'Unit_Price'] = round(data['Unit_Price']/(10000*0.3025),4)

# data["Unit_Price"].value_counts(dropna=False)
data = data.replace({'Unit_Price':{NAN:0}}, regex=True)


data.loc[:,'DRPD_TargetX'] = round(data["Trading_Target_X"],4)
data.loc[:,'DRPD_TargetY'] = round(data["Trading_Target_Y"],4)

data.loc[(~data['Trading_Target'].isin(['土地','車位']) & data['Building_Type'].isin(['公寓(5樓含以下無電梯)']) ) , 'DRPD_BuildingTypeFlag'] = '01'
data.loc[(~data['Trading_Target'].isin(['土地','車位']) & ((data['Building_Type'].isin(['住宅大樓(11層含以上有電梯)'])) | (data['Building_Type'].isin(['華廈(10層含以下有電梯)'])))) & (data["DRPD_BuildingTypeFlag"]=="na") , 'DRPD_BuildingTypeFlag'] = '02'
data.loc[(~data['Trading_Target'].isin(['土地','車位']) & data['Building_Type'].isin(['透天厝'])) & (data["DRPD_BuildingTypeFlag"]=='na') , 'DRPD_BuildingTypeFlag'] = '03'
data.loc[(data["DRPD_BuildingTypeFlag"]=='na') , 'DRPD_BuildingTypeFlag'] = '04'

# data["Unit_Price"].value_counts(dropna=False)
# data["Total_Price"].value_counts(dropna=False)
data["DRPD_BuildingTypeFlag"].value_counts(dropna=False)
# data["Building_Type"].value_counts(dropna=False)

data.loc[data["DRPD_BuildingTypeFlag"].isin(['01']) & data['DRPD_BuildingAge'].between(0,10,inclusive='both'), 'DRPD_BuildingSeg'] = '01'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['01']) & data['DRPD_BuildingAge'].between(11,20,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '03'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['01']) & data['DRPD_BuildingAge'].between(21,999,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '04'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['02']) & data['DRPD_BuildingAge'].between(0,10,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '06'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['02']) & data['DRPD_BuildingAge'].between(11,20,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '08'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['02']) & data['DRPD_BuildingAge'].between(21,999,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '09'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['03']) & data['DRPD_BuildingAge'].between(0,10,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '16'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['03']) & data['DRPD_BuildingAge'].between(11,20,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '18'
data.loc[(data["DRPD_BuildingTypeFlag"].isin(['03']) & data['DRPD_BuildingAge'].between(21,999,inclusive='both')) & (data['DRPD_BuildingSeg']=='na'), 'DRPD_BuildingSeg'] = '19'
data.loc[(data['DRPD_BuildingSeg']=='na') , 'DRPD_BuildingSeg'] = '99'

data["DRPD_BuildingSeg"].value_counts(dropna=False)
# a=data.loc[:,["DRPD_BuildingSeg",'DRPD_BuildingAge']].value_counts()

zip_code = pd.read_excel(r'D:\Users\z00188600\AppData\Local\anaconda3\Lib\site-packages\ctbc_project\ZIP.xlsx',dtype=str).rename(columns={'city':'City','town':'District'})

data = pd.merge(left = data, right=zip_code,on=['City','District'], how = 'left')

# addr_replace = '|'.join((zip_code["City"] + zip_code["District"]).tolist())

# b = data["Address"].str.split(addr_replace,expand=True).replace({pd.NA:""})
# c = b[0]
# b = b.loc[:,[_ for _ in b if _ != 0]]
# for key in b :
#     c = c + b[key] 
    
# data.loc[:,["Address"]] = c

data = data.reset_index().rename(columns={'index':'DRPD_Sequence'})

# data['Geom'] = ""

data = data.rename(columns=dgiskey)
data.columns
data = data.drop([ _ for _ in data if _ not in dgiskey_lis] ,axis=1)

data.loc[:,[ _ for _ in dgiskey_lis if _ not in data]] = ""

data[['DRPD_Number','DRPD_TargetX','DRPD_TargetY']].to_csv(join(wb, 'GEOM_CTBC_RealPriceDetail_XY.csv'), sep="|", index = False, encoding = 'utf8')
# 把XY匯出，用本機SAS去跑fishID，跑完存成GEOM_CTBC_RealPriceDetail_fishid.xlsx


fishid = pd.read_excel(join(wb, 'GEOM_CTBC_RealPriceDetail_fishid.xlsx'),dtype=str)
# 把本機跑完的結果，讀取進來，繼續後面的併檔

data = pd.merge(left = data, right=fishid[["DRPD_Number",'DRPD_FishId']],on=['DRPD_Number'], how = 'left')

if True in (data['DRPD_BuildingSeg']=='na').tolist():
    print("Column name DRPD_BuildingSeg is ERROR")
elif True in (data['DRPD_BuildingTypeFlag']=='na').tolist():
    print("Column name DRPD_BuildingTypeFlag is ERROR")
elif len(data.columns) != 36 :
    print("Column length is ERROR")
else:
    data.to_csv(join(wb,fileSend), sep="|", index = False, encoding = 'utf8')
    picklesave(data, join(wb, 'realestate_send') )
# 匯出資料跑到這裡================================================================


# 加工回來=======================================================================
data_complete = pd.read_csv(join(wb_processing,fileTotal), dtype = str, delimiter="|", encoding='utf8')
data_complete["DRPD_EParkingPrice"].unique()#不能有N、Y 
data_complete['DRPD_ModifyFlag'].unique()   #只能有N、Y
data_complete['DRPD_SpecialTradeFlag'].unique()   #只能有N、Y
