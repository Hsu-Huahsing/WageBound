# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 09:24:36 2024

@author: Z00051711
"""
import json
import pandas as pd
from os.path import join
from ctbc_project.config import comparecase_clean,comparecase_select
from StevenTricks.fileop import PathWalk_df


clean_colname = {
    "SimilarityFlag":"Similarityflag",
    }

        
actualprice_path = r"D:\DGIS\workbench\202407\GEOM_CTBC_RealPriceDetail_stall.csv"
actualprice = pd.read_csv(actualprice_path,sep="|")
temp_path = r'C:\Users\z00188600\Desktop'

for file in ["LV3"]:
    with open(join(temp_path,file+".json"), encoding="utf-8") as f:
        temp_data = json.load(f)
        
        collateral = pd.DataFrame()
        case_ctbc = pd.DataFrame()
        case_lvr = pd.DataFrame()
        
        upload = temp_data['CollateralData']
        output = temp_data['Result']
        
        appnbr = upload["CaseNo"]
        colnbr = upload["CollateralNo"]
        
        # try:
        #     upload = json.loads(upload)
        #     output = json.loads(output.replace('\'', '"').replace("A\"MORE社區", "A'MORE社區").replace("C\"EST LA VIE", "C'EST LA VIE"))
        # except:
            
        #     # break
        #     continue
    
        # a = temp_data.head(2)
    
        # upload = upload['CollateralData']
        
        comparecase = comparecase_select(output.pop('CompareCase'))
        output['CompareCase'] = comparecase_clean(comparecase, AppNbr=appnbr,CollNbr=str(colnbr))
        
        upload = pd.DataFrame([upload])
        
        ctbc = pd.DataFrame(output['CompareCase']['CTBC_Inside'])
        lvr = pd.DataFrame(output['CompareCase']['LVR'])
        
        upload = upload.rename(columns=clean_colname)
        # upload["CaseNo"] = appnbr
        # upload["CollateralNo"] = str(colnbr)
        ctbc = ctbc.rename(columns=clean_colname)
        lvr = lvr.rename(columns=clean_colname)
        
        collateral = pd.concat([collateral,upload])
        case_ctbc = pd.concat([case_ctbc,ctbc])
        case_lvr = pd.concat([case_lvr, lvr])
        case_lvr = pd.merge(case_lvr, actualprice[["DRPD_Number","DRPD_SpecialTradeFlag"]].rename(columns={"DRPD_Number":"Id"}),on="Id",how="left")
        # temp_data["number"]
        # temp_data["application_nbr"]
        
        print(appnbr)
        
        print(file)
        
        with pd.ExcelWriter(join(temp_path, '相似度分析{}.xlsx'.format(file))) as writer:
            collateral.to_excel(writer, sheet_name='collateral', index=False)
            case_ctbc.to_excel(writer, sheet_name='ctbc_inside', index=False)
            case_lvr.to_excel(writer, sheet_name='lvr', index=False)


df_path = PathWalk_df(temp_path,fileinclude=["相似度分析"],fileexclude=[".zip","統整"])

collateral = pd.DataFrame()
case_ctbc = pd.DataFrame()
case_lvr = pd.DataFrame()
for path_file in df_path["path"]:
    df = pd.read_excel(path_file,sheet_name=None)
    collateral = pd.concat([collateral,df["collateral"]])
    case_ctbc = pd.concat([case_ctbc,df["ctbc_inside"]])
    case_lvr = pd.concat([case_lvr,df["lvr"]])

with pd.ExcelWriter(join(temp_path, '相似度分析_統整.xlsx')) as writer:
    collateral.to_excel(writer, sheet_name='collateral', index=False)
    case_ctbc.to_excel(writer, sheet_name='ctbc_inside', index=False)
    case_lvr.to_excel(writer, sheet_name='lvr', index=False)
    