# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 16:56:27 2023

@author: Z00051711
"""
from copy import deepcopy
from numpy import NAN,floor
from os.path import join, abspath, dirname, isfile, pardir, samefile
from os import makedirs, walk

import pickle
import pandas as pd
import datetime 

path_xy = r"C:\Users\z00188600\Desktop\DGIS移轉\FishID.xlsx"
data_xy = pd.read_excel(path_xy, dtype = str)

colname = {
    '建物':{
        '編號':'Number',
        '主要用途':'Building_Main_Use',
        '主要建材':'Building_Main_Material',
        '建物移轉總面積(平方公尺)':'Trans_Area',
        '屋齡':'Building_Age',
        '建物移轉面積(平方公尺)':'Building_Trans_Area',
        '建物移轉面積平方公尺':'Building_Trans_Area',
        '建物完成日期':'Building_Completion_Date',
        '建築完成日期':'Building_Completion_Date',
        '總層數':'Building_Total_Floor',
        '建物分層':'Building_layer'
        },
    '不動產買賣':{
        '行政區':'City',
        '鄉鎮市區':'District',
        '交易標的':'Trading_Target',
        '土地區段位置/建物區段門牌':'Address',
        '土地區段位置/建物門牌':'Address',
        '土地位置/建物門牌':'Address',
        '土地移轉總面積(平方公尺)':'Land_Trans_Area',
        '都市土地使用分區':'Land_use_Type',
        '非都市土地使用分區':'Non_urban_District',
        '非都市土地使用編定':'Non_urban_Land',
        '交易年月日':'Trading_Date',
        '交易筆棟數':'Transactions',
        '移轉層次':'Trans_Floor',
        '總樓層數':'Total_Floor',
        '建物型態':'Building_Type',
        '主要用途':'Main_Use',
        '主要建材':'Main_Material',
        '建築完成年月':'Completion_Date',
        '建物移轉總面積(平方公尺)':'Trans_Area',
        '建物現況格局-房':'Layout_Bedroom',
        '建物現況格局-廳':'Layout_Livroom',
        '建物現況格局-衛':'Layout_Bathroom',
        '建物現況格局-隔間':'Partition_YN',
        '有無管理組織':'Management_YN',
        '總價(元)':'Total_Price',
        '單價(元/平方公尺)':'Unit_Price',
        '車位類別':'Stall_Type',
        '車位移轉總面積(平方公尺)':'Stall_trans_area',
        '車位總價(元)':'Stall_Total_Price',
        '交易標的橫坐標':'Trading_Target_X',
        '交易標的縱坐標':'Trading_Target_Y',
        '有無備註欄(Y/N)':'Note_YN',
        '備註':'Note',
        '編號':'Number',
        '屋齡':'Building_Age',
        '建物移轉面積(平方公尺)':'Building_Trans_Area',
        '總層數':'Building_Total_Floor',
        '建物分層':'Building_layer'
        }
    }

dropcol = {
    '不動產買賣':[
        '主建物面積','附屬建物面積','陽台面積','電梯'
        ]
    }

cityname = {
    'A':'台北市',
    'B':'台中市',
    'C':'基隆市',
    'D':'台南市',
    'E':'高雄市',
    'F':'新北市',
    'G':'宜蘭縣',
    'H':'桃園市',
    'I':'嘉義市',
    'J':'新竹縣',
    'K':'苗栗縣',
    'M':'南投縣',
    'N':'彰化縣',
    'O':'新竹市',
    'P':'雲林縣',
    'Q':'嘉義縣',
    'T':'屏東縣',
    'U':'花蓮縣',
    'V':'台東縣',
    'W':'金門縣',
    'X':'澎湖縣',
    'Z':'連江縣',
}
																		
dgiskey = {
    'City':'DRPD_City',
    'District':'DRPD_District',
    'Trading_Target':'DRPD_TradeTarget',
    'Address':'DRPD_Address',
    'Land_Trans_Area':'DRPD_LandTransArea',
    'Land_use_Type':'DRPD_LandUseType',
    'Non_urban_District':'DRPD_NonUrbanDistrict',
    'Non_urban_Land':'DRPD_NonUrbanland',
    'Trading_Date':'DRPD_TradeDate',
    'Transactions':'DRPD_Transactions',
    'Trans_Floor':'DRPD_TransFloor',
    'Total_Floor':'DRPD_TotalFloor',
    'Building_Type':'DRPD_BuildingType',
    'Main_Use':'DRPD_MainPurpose',
    'Main_Material':'DRPD_MainMaterial',
    'Completion_Date':'DRPD_CompletionDate',
    'Trans_Area':'DRPD_TransArea',
    'Layout_Bedroom':'DRPD_LayoutBedroom',
    'Layout_Livroom':'DRPD_LayoutLivroom',
    'Layout_Bathroom':'DRPD_LayoutBathroom',
    'Total_Price':'DRPD_TotalPrice',
    'Unit_Price':'DRPD_UnitPrice',
    'Note':'DRPD_Note',
    'Number':'DRPD_Number',
    'FishID':'DRPD_FishId',
    'zip':"DRPD_ZipCode"
    }

dgiskey_lis = ['DRPD_Sequence', 
               'Geom', 
               'DRPD_ZipCode', 
               'DRPD_City', 
               'DRPD_District',
               'DRPD_TradeTarget', 
               'DRPD_Address', 
               'DRPD_LandTransArea',
               'DRPD_LandUseType', 
               'DRPD_NonUrbanDistrict', 
               'DRPD_NonUrbanland',
               'DRPD_TradeDate', 
               'DRPD_Transactions', 
               'DRPD_TransFloor',
               'DRPD_TotalFloor', 
               'DRPD_BuildingType', 
               'DRPD_BuildingTypeFlag',
               'DRPD_MainPurpose', 
               'DRPD_MainMaterial', 
               'DRPD_CompletionDate',
               'DRPD_TransArea', 
               'DRPD_LayoutBedroom', 
               'DRPD_LayoutLivroom',
               'DRPD_LayoutBathroom', 
               'DRPD_Partition', 
               'DRPD_Management',
               'DRPD_TotalPrice', 
               'DRPD_UnitPrice', 
               'DRPD_TargetX', 
               'DRPD_TargetY', 
               'DRPD_HasNote', 
               'DRPD_Note',
               'DRPD_Number', 
               'DRPD_BuildingSeg', 
               'DRPD_BuildingAge', 
               ]


def fishID_get(source = pd.DataFrame(),col_x="",col_y=""):    
    lis = list(range(100,1100,200))

    x = (pd.to_numeric(source[col_x])*0.001 - floor(pd.to_numeric(source[col_x])*0.001))*1000
    y = (pd.to_numeric(source[col_y])*0.001 - floor(pd.to_numeric(source[col_y])*0.001))*1000

    x[x<100] = 100
    y[y<100] = 100

    for n in [0,1,2,3] :
        x[x.between(lis[n],lis[n+1],inclusive='right') & (x>(lis[n]+lis[n+1])/2)]=lis[n+1]
        x[x.between(lis[n],lis[n+1],inclusive='right') & (x<=(lis[n]+lis[n+1])/2)]=lis[n]
    
        y[y.between(lis[n],lis[n+1],inclusive='right') & (y>(lis[n]+lis[n+1])/2)]=lis[n+1]
        y[y.between(lis[n],lis[n+1],inclusive='right') & (y<=(lis[n]+lis[n+1])/2)]=lis[n]

    x[x>900] = 900
    y[y>900] = 900

    x = floor(pd.to_numeric(source[col_x])*0.001)*1000 + x
    y = floor(pd.to_numeric(source[col_y])*0.001)*1000 + y

    df_temp = pd.DataFrame({"P_X":x.map(lambda x : str(x).split('.')[0]),"P_Y":y.map(lambda x : str(x).split('.')[0])})

    df_temp = pd.merge(df_temp, data_xy,on=["P_X","P_Y"], how='left')

    df_temp = df_temp.fillna('0')

    source["DRPD_FishId"] = df_temp["FishID"]
    
    return source

# test = deepcopy(fishid[["DRPD_TargetX","DRPD_TargetY"]])

# test = fishID_get(test,"DRPD_TargetX","DRPD_TargetY")

# fishid.loc[fishid['DRPD_FishId'] != test['DRPD_FishId'],:]

def picklesave(data, path):
    # path要精確到檔名
    makedirs(abspath(dirname(path)), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(data, f)


def pickleload(path):
    # path要精確到檔名
    with open(path, 'rb') as f:
        data = pickle.load(f)
        return data
    
    
def pathlevel(left, right):
    if isfile(right) is True:
        right = abspath(join(right, pardir))
    if len(left) > len(right):
        return
    level = 0
    while not samefile(left, right):
        right = abspath(join(right, pardir))
        level += 1
    return level


def PathWalk_df(path, dirinclude=[], direxclude=[], fileexclude=[], fileinclude=[], level=None):
    res = []
    for _path, dire, file in walk(path):
        if not dire and not file:
            res.append([None, path])
        for f in file:
            res.append([f, join(_path, f)])
        
    res = pd.DataFrame(res, columns=["file", "path"])
    res.loc[:, 'level'] = res['path'].map(lambda x: pathlevel(path, x))
    if level is not None:
        res = res.loc[res['level'] <= level]
    
    res = res.loc[res["path"].str.contains("\\|\\".join(dirinclude), na=False)]
    if direxclude:
        res = res.loc[~(res["path"].str.contains("\\|\\".join(direxclude), na=True))]
    res = res.loc[res.loc[:, "file"].str.contains("|".join(fileinclude), na=False)]
    if fileexclude:
        res = res.loc[~(res.loc[:, "file"].str.contains("|".join(fileexclude), na=True))]
    return res.reset_index(drop=True)


def strtodate(x):
    # 0820412轉成1993/04/12
    if pd.isna(x) is True:
        return
    x = str(x).split(".")[0]
    x = x.replace(" ","").replace('-','')
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

# ==============================================================================
# 以下前置作業
td = datetime.date.today()

date_3m = 1130101  #要+一個月
d = pd.date_range(start="2021-4", periods=38, freq="MS")  #要+一個月
d1 = max(d).strftime("%Y-%m-%d") 
d2 = min(d).strftime("%Y-%m-%d") 

path = r'D:\DGIS\原始資料\{}'.format(max(d).strftime("%Y%m") )
wb = r'D:\DGIS\workbench\{}'.format(max(d).strftime("%Y%m") )
wb_processing = r'D:\DGIS\workbench\{}\processing'.format(max(d).strftime("%Y%m") )

makedirs(path, exist_ok=True) , makedirs(wb, exist_ok=True), makedirs(wb_processing, exist_ok=True)

fileTotal = r'GEOM_CTBC_RealPriceDetail.csv'
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
# 先把原始檔存起來

data = deepcopy(res["不動產買賣"])
del res

data.loc[:,['Trading_Date','Completion_Date']] = data[['Trading_Date','Completion_Date']].applymap(lambda x : strtodate(x))

picklesave(data, join(wb, 'realestate_date') )
# 因為轉日期要轉很久，所以轉完先存起來

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

zip_code = pd.read_excel(r'D:\Users\z00188600\AppData\Local\anaconda3\Lib\site-packages\ctbc_project\ZIP.xlsx',dtype=str).rename(columns={'city':'City','town':'District'})

data = pd.merge(left = data, right=zip_code,on=['City','District'], how = 'left')

data = data.reset_index().rename(columns={'index':'DRPD_Sequence'})

data = data.rename(columns=dgiskey)

data = data.drop([ _ for _ in data if _ not in dgiskey_lis] ,axis=1)

data.loc[:,[ _ for _ in dgiskey_lis if _ not in data]] = ""

data = fishID_get(source=data,col_x="DRPD_TargetX",col_y="DRPD_TargetY")
# 用function去算出fish id

# data[['DRPD_Number','DRPD_TargetX','DRPD_TargetY']].to_csv(join(wb, 'GEOM_CTBC_RealPriceDetail_XY.csv'), sep="|", index = False, encoding = 'utf8')
# 把XY匯出，用本機SAS去跑fishID，跑完存成GEOM_CTBC_RealPriceDetail_fishid.xlsx

# fishid = pd.read_excel(join(wb, 'GEOM_CTBC_RealPriceDetail_fishid.xlsx'),dtype=str)
# 把本機跑完的結果，讀取進來，繼續後面的併檔

# data = pd.merge(left = data, right=fishid[["DRPD_Number",'DRPD_FishId']],on=['DRPD_Number'], how = 'left')

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
data_complete["DRPD_TradeDate"] = data_complete["DRPD_TradeDate"].str.split(" ",expand=True)[0]
data_complete.to_csv(join(wb_processing,fileTotal), sep="|", index = False, encoding = 'utf8')
data_complete["DRPD_EParkingPrice"].unique()#不能有N、Y 
data_complete['DRPD_ModifyFlag'].unique()   #只能有N、Y
data_complete['DRPD_SpecialTradeFlag'].unique()   #只能有N、Y

