# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 14:13:18 2024

@author: Z00051711
"""

import pandas as pd
from os.path import join,exists
import json
import requests as re
import ast
import time
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from StevenTricks.fileop import pickleload,picklesave
from ctbc_project.config import comparecase_select,clean_colname

datapath = r"D:\數位專案\透天房地分離\2025_6RC\驗證用"
datapath = r"E:\數位專案\HPM2.0\2025-11RC\改辦法\驗證用資料"
path_jsonoutput = join(datapath,"jsonoutput")
path_source = r"DGIS_InOutJson_0913.xlsx"
Type = "uat"
# Type = "sit"
# ===========================================================================
# ==前置作業
# ===========================================================================


url_dict = {
    "sit" : r"http://dgisapiuat.ctbcbank.com:8080/dgis/dgisapi/AccurateEstimation"  ,
    "uat" : r"http://dgisapiuat.ctbcbank.com/dgis/dgisapi/AccurateEstimation"
}

path_apiresult = r"{}Result.pkl".format(Type)

def call_api(lis):
    res = re.post(url_dict[Type], json=lis)
    resjson = res.json()
    # print(resjson)
    # print(resjson["Success"])
    # time_cost = res.elapsed.total_seconds()
    if resjson["Success"] == False :
        caseno = lis["CollateralData"]["CaseNo"]
        collateralno = lis["CollateralData"]["CollateralNo"]
        conn = False
    else :
        caseno = resjson["Result"]["CaseNo"]
        collateralno = resjson["Result"]["CollateralNo"]
        conn = True
    return [caseno,collateralno,resjson,lis,conn]

def dict_to_df(dict_input):
    temp = pd.DataFrame()
    for _ in dict_input :
        temp = pd.concat([temp,pd.DataFrame([_["properties"]])])
    return temp

# 不管如何都要先把source讀取進來
if exists(join(datapath,"source.pkl")) is True:
    data = pickleload(join(datapath,"source.pkl"))
else:
    data = pd.read_excel(join(datapath,path_source))
    picklesave(data, join(datapath,"source.pkl"))

# 沒有api_result就自己打一個出來
if exists(join(datapath,path_apiresult)) is True :
    apiresult = pickleload(r"C:\Users\z00188600\Desktop\uatResult.pkl")
    # apiresult = pickleload(join(datapath,path_apiresult))
    res = pd.DataFrame(apiresult,columns=["caseno","collateralno","output_json","input_json","res"])
    res = res.loc[res["caseno"].isin(["20240603EI00064_0"])]
    for applno ,collateralno, apioutput, input_data, conn in res.values:
        with open(join(path_jsonoutput,"{}.txt".format(applno)) , "w", encoding='utf-8') as f:
            f.write(str(apioutput))
else :
    dgisinput = pd.DataFrame()
    
    for applno,inputjson in data[['ApplNo','InputJson']].values:
        j_data = json.loads(inputjson)
        
        collateral_data = pd.DataFrame([j_data["CollateralData"]])
        # if collateral_data.empty is True :
        #     break
        collateral_data["applno_RawData"] = applno #applno_RawData
        # print(collateral_data)
        dgisinput = pd.concat([dgisinput,collateral_data])
       
    apiresult = []
    maxWorkersNum = 10
    apiinput = data['InputJson'].apply(lambda x : json.loads(x)).tolist()
    
    for dic in apiinput:
        if "CommunityFlag" not in dic["CollateralData"] :
            dic["CollateralData"]["CommunityFlag"] = ""
        
    
    print('10.5.3 API, start calling...')
    print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    
    start = datetime.now()
    with ThreadPoolExecutor(max_workers=maxWorkersNum) as pool:  # 多線呈主控，設定線呈數量與執行環境
        apiresult = list(tqdm(pool.map(call_api, apiinput[:1000])))  # 迴圈帶入input並執行函數
    mid = datetime.now()
    
    picklesave(apiresult, join(datapath,path_apiresult))

lvr_out = pd.DataFrame()
ctbc_inside_out = pd.DataFrame()
pcsm_input = pd.DataFrame()
pcsm_output = pd.DataFrame()

for applno ,collateralno, apioutput, input_data, conn in apiresult:
    
    if conn is False:
        print("conn :",conn )
        print(applno)
        continue
    
    pcsm = apioutput["PerformanceStatistic"]
    
    if "PCSMINPUT" not in pcsm or "PCSMOUTPUT" not in pcsm:
        print("PCSM ERROR :" )
        print(applno)
        continue
    if "applno" in pcsm_input:
        if (applno in pcsm_input["applno"]) & (collateralno in pcsm_input["CollateralNo"]) : 
            continue
    
    
    pcsm_input_temp = pd.DataFrame([pcsm["PCSMINPUT"]])
    pcsm_output_temp = pd.DataFrame([pcsm["PCSMOUTPUT"]])
    pcsm_input_temp["applno"] = applno
    pcsm_input_temp["CollateralNo"] = collateralno
    pcsm_output_temp["applno"] = applno
    pcsm_output_temp["CollateralNo"] = collateralno
    
    comparecase = comparecase_select(apioutput["Result"]["CompareCase"])
    lvr = dict_to_df(comparecase["LVR"])
    ctbc_indside = dict_to_df(comparecase["CTBC_Inside"])
    
    lvr["applno"] = applno
    lvr["CollateralNo"] = collateralno
    ctbc_indside["applno"] = applno
    ctbc_indside["CollateralNo"] = collateralno
    
    lvr_out = pd.concat([lvr_out,lvr])
    ctbc_inside_out = pd.concat([ctbc_inside_out,ctbc_indside])
    
    pcsm_input = pd.concat([pcsm_input,pcsm_input_temp])
    pcsm_output = pd.concat([pcsm_output,pcsm_output_temp])
    
    # if applno == "20240510EI00094_0" : break

dict_col = ["H02", "T1ScoreResult", "T2ScoreResult"]
list_col = ["ParkingSpaces"]

pcsm_input = pcsm_input.drop_duplicates(subset=[_ for _ in pcsm_input if _ not in dict_col], ignore_index=True)
pcsm_output = pcsm_output.drop_duplicates(subset=[_ for _ in pcsm_output if _ not in dict_col], ignore_index=True)

pcsm_applno = list(pcsm_output["applno"]+pcsm_output["CollateralNo"])+list(pcsm_input["applno"]+pcsm_input["CollateralNo"])
pcsm_applno = list(set(pcsm_applno))

with pd.ExcelWriter(join(datapath, 'LOG_PCSM_{}.xlsx'.format(Type))) as writer:
    pcsm_input = pcsm_input.rename(columns=clean_colname)
    pcsm_output = pcsm_output.rename(columns=clean_colname)
    pcsm_input.to_excel(writer, sheet_name='pcsm_input', index=False)
    pcsm_output.to_excel(writer, sheet_name='pcsm_output', index=False)
    
    
dgisinput_part = dgisinput.loc[(dgisinput["CaseNo"]+dgisinput["CollateralNo"]).isin(pcsm_applno),:]
lvr_out_part = lvr_out.loc[(lvr_out["applno"]+lvr_out["CollateralNo"]).isin(pcsm_applno),:]
ctbc_inside_out_part = ctbc_inside_out.loc[(ctbc_inside_out["applno"]+ctbc_inside_out["CollateralNo"]).isin(pcsm_applno),:]

dgisinput_part = dgisinput_part.drop_duplicates(subset=[_ for _ in dgisinput_part if _ not in list_col], ignore_index=True)
lvr_out_part = lvr_out_part.drop_duplicates(ignore_index=True)
ctbc_inside_out_part = ctbc_inside_out_part.drop_duplicates()

with pd.ExcelWriter(join(datapath, 'LOG_Collateral_{}.xlsx'.format(Type))) as writer:
    dgisinput_part = dgisinput_part.rename(columns=clean_colname)
    lvr_out_part = lvr_out_part.rename(columns=clean_colname)
    ctbc_inside_out_part = ctbc_inside_out_part.rename(columns=clean_colname)
    dgisinput_part.to_excel(writer, sheet_name='Collateral', index=False)
    lvr_out_part.to_excel(writer, sheet_name='LVR', index=False)
    ctbc_inside_out_part.to_excel(writer, sheet_name='ctbc_inside', index=False)


# =============================================================================
# 以下驗證用
# =============================================================================

data1 = data.loc[data["ApplNo"]=="20240605EI00189",:]
data2 = data.loc[data["ApplNo"]=="20240702EL00004",:]
def call_api_test(lis):
    res = re.post(url_dict[Type], json=lis)
    resjson = res.json()
    return resjson
apiresult["caseno"]
apiresult = pd.DataFrame(apiresult,columns=["caseno","collateralno","output_json","input_json","res"])
data_test = apiresult.loc[apiresult["caseno"]=="20240527EI00084_0",:]
output = str(data_test["input_json"][0])
input_text = str(data_test["input_json"][0])
test = call_api_test(lis=json.loads(data_test))
