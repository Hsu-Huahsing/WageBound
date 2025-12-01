# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 09:24:36 2024

@author: Z00051711

解譯LOG專用
"""
import json
import ast
import pandas as pd
from os.path import join
from ctbc_project.config import comparecase_select,clean_colname
from StevenTricks.file_utils import PathWalk_df

temp_path = r'D:\數位專案\透天房地分離\上線後\202501LOG'
temp_path = r'D:\數位專案\透天房地分離\2025_6RC\上線日測試'
temp_path = r'E:\數位專案\HPM2.0\2025-6RC\上線後監控\202508案例\LOG'
temp_path = r'C:\Users\z00188600\Desktop\test'
temp_path = r'\\w80770616\個金風險政策部\99.各科\01.擔保\05.房貸PCO\驗證報告\202511_HPM2透天及策略優化\上線日'
# 把.txt丟到上面這個路徑，就可以直接跑

def dict_to_df(dict_input):
    temp = pd.DataFrame()
    for _ in dict_input :
        temp = pd.concat([temp,pd.DataFrame([_["properties"]])])
    return temp

# clean_colname = {
#     "SimilarityFlag":"Similarityflag",
#     }

replaceWordList = [["A\"MORE社區", "A'MORE社區"], ["C\"EST LA VIE", "C'EST LA VIE"],["4\'33\'\'","4分33秒"],["4\"33\"\"","4分33秒"]]

df_path = PathWalk_df(temp_path,fileinclude=[".txt"])

df = pd.DataFrame()


lvr_out_excel = pd.DataFrame()
ctbc_inside_out_excel = pd.DataFrame()
pcsm_input_excel = pd.DataFrame()
pcsm_output_excel = pd.DataFrame()
dgisinput_excel = pd.DataFrame()
result_excel = pd.DataFrame()

for path in df_path["path"]:
    lvr_out = pd.DataFrame()
    ctbc_inside_out = pd.DataFrame()
    pcsm_input = pd.DataFrame()
    pcsm_output = pd.DataFrame()
    dgisinput = pd.DataFrame()
    result = pd.DataFrame()
    # with open(path, 'r', encoding="utf-8") as f:
    with open(path, 'rb') as f:
        logList = [x.decode('utf8').strip() for x in f.readlines()]
        # for line in f:
        #     print(line.decode(errors='ignore'))
        
        # logList = f.read().decode(errors='replace')
        # logList = f.readlines()
    
    ApplNo = logList[0].split(':')[-1][:]
    # print(ApplNo)
    ApplNoB = logList[1].split(':')[-1][:]
    GuaraNo = logList[2].split(':')[-1][:]
    
    Input = logList[3][6:]
    inputJson = ast.literal_eval(Input)
    
    OutPut = logList[5][7:].replace('\'', '"')
    
    for targetWords, replaceWords in replaceWordList:
        OutPut = OutPut.replace(targetWords, replaceWords)
    OutPutJson = json.loads(OutPut)
    
    dgisinput = pd.concat([pd.DataFrame([inputJson["CollateralData"]]),pd.DataFrame([inputJson["Location"]])],axis=1)
    comparecase = comparecase_select(OutPutJson["Result"]["CompareCase"])
    lvr_out = dict_to_df(comparecase["LVR"])
    ctbc_inside_out = dict_to_df(comparecase["CTBC_Inside"])
    
    result = pd.DataFrame([OutPutJson["Result"]]).drop(["ResultFile"],errors="ignore")
    result = pd.concat([result,pd.DataFrame([OutPutJson["Result"]["ResultFile"]])], axis=1)
    
    if "PerformanceStatistic" in OutPutJson:
        pcsm_input = pd.DataFrame([OutPutJson["PerformanceStatistic"]["PCSMINPUT"]])
        pcsm_output = pd.DataFrame([OutPutJson["PerformanceStatistic"]["PCSMOUTPUT"]])
    
        pcsm_input["applno"] = ApplNo
        # print(ApplNo,"=========================")
        pcsm_output["applno"] = ApplNo
        pcsm_output["CollateralNo"] = GuaraNo
        
        pcsm_input = pcsm_input.rename(columns=clean_colname)
    
    result["applno"] = ApplNo
    result["CollateralNo"] = GuaraNo
        
    lvr_out["applno"] = ApplNo
    ctbc_inside_out["applno"] = ApplNo
    lvr_out["CollateralNo"] = GuaraNo
    ctbc_inside_out["CollateralNo"] = GuaraNo
    dgisinput["applno"] = ApplNo
    dgisinput["ZipCode"] = OutPutJson["Result"]["ZipCode"]
    
    lvr_out = lvr_out.rename(columns=clean_colname)
    dgisinput = dgisinput.rename(columns=clean_colname)
    ctbc_inside_out = ctbc_inside_out.rename(columns=clean_colname)
    pcsm_input = pcsm_input.rename(columns=clean_colname)
    # print(pcsm_input["applno"],"++++++++++++++++++++++++++++++++++++")
    pcsm_output = pcsm_output.rename(columns=clean_colname)
    result = result.rename(columns=clean_colname)
    
    dgisinput_excel = pd.concat([dgisinput_excel,dgisinput])
    lvr_out_excel = pd.concat([lvr_out_excel,lvr_out])
    ctbc_inside_out_excel = pd.concat([ctbc_inside_out_excel,ctbc_inside_out])
    pcsm_input_excel = pd.concat([pcsm_input_excel,pcsm_input])
    pcsm_output_excel = pd.concat([pcsm_output_excel,pcsm_output])
    result_excel = pd.concat([result_excel,result])

with pd.ExcelWriter(join(temp_path, 'LOG_Collateral_uat.xlsx')) as writer:
    dgisinput_excel.to_excel(writer, sheet_name='Collateral', index=False)
    lvr_out_excel.to_excel(writer, sheet_name='LVR', index=False)
    ctbc_inside_out_excel.to_excel(writer, sheet_name='ctbc_inside', index=False)
    
with pd.ExcelWriter(join(temp_path, 'LOG_PCSM_uat.xlsx')) as writer:
    pcsm_input_excel.to_excel(writer, sheet_name='pcsm_input', index=False)
    pcsm_output_excel.to_excel(writer, sheet_name='pcsm_output', index=False)
    result_excel.to_excel(writer, sheet_name='result', index=False)



# R5LOG_excel = pd.concat([dgisinput_excel[["applno","ZipCode","OAddr","HouseType",]], pcsm_input_excel[["BuildingType"]], pcsm_output_excel[["pcsm_output_excel","HierachyFlag"]]])
# with pd.ExcelWriter(join(temp_path, 'R5_test.xlsx')) as writer:
#     R5LOG_excel.to_excel(writer, sheet_name='LOG', index=False)

# with open(r"C:\Users\z00188600\Desktop\新文字文件.txt", 'r', encoding="utf-8") as f:
#     logList = f.readlines()
# inputJson = ast.literal_eval(logList)
# for targetWords, replaceWords in replaceWordList:
#     OutPut = OutPut.replace(targetWords, replaceWords)
# OutPutJson = json.loads(logList[0])    
# df = pd.DataFrame()
# df_out = pd.DataFrame()
# for c in OutPutJson["FeatureData"]["features"]:
#     df = pd.DataFrame([c["properties"]])
#     df_out = pd.concat([df_out,df])
# df_out.to_csv(r"C:\Users\z00188600\Desktop\新文字文件.csv", index = False, encoding = 'big5')
