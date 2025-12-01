# -*- coding: utf-8 -*-
"""
Created on Thu Nov  9 15:50:49 2023

@author: Z00054570
"""

import pandas as pd
from requests import post
#  import sys
from tqdm import tqdm
# sys.path.append('../..')
# from app.Garage.util import *

def get_community(address, Zip_code):
    add_data = {
        "SystemId": "NUMS", 
        "TransNum":"7108AF85-7EC5-48D8-9174-CEADD52E6F8B",
        "TransDate":"20231108",
        "ZipCode": Zip_code,
        "LocationAdd":address
    }
    
    # 地址找社區
    r = post('http://172.24.15.230/DGISAdressMatch/adressMatchApi/AdressMatchAreaName/AdressMatchAreaName', json=add_data)
    if r.json()["SystemId"]:
        result = r.json()
        return result
    else:
        return r.json()

df = pd.read_csv(r"E:\車位自動化拆分專案\地址比對社區\地址比對清單.csv", encoding='Big5')


print('>> 開始比對...')
for idx, row in tqdm(df.iterrows()):
    
    out_json = get_community(row['add'], row['Zip_Code'])  
    # 地址欄位 郵遞區號欄位
    
    df.loc[idx, 'DCDL_BuildingKey'] = out_json['CommunityNbr']
    df.loc[idx, 'DCDL_CollateralName'] = out_json['CommunityName']
    # df.loc[idx, 'Out_ResponseNo'] = out_json['ResponseNo']    

df.to_excel(r'E:\車位自動化拆分專案\地址比對社區\outputfile\Case_CmUpdate2.xlsx', encoding='utf-8')
print('>> 完成比對與輸出!!!')