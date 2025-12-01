# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 14:36:55 2024

@author: Z00051711
"""

import pandas as pd
from os.path import join
from StevenTricks.fileop import PathWalk_df

temp_path = r'D:\轉檔\nums_application資料清理\10AH25YA23TA_AU_資料匯入9至16'

df_path = PathWalk_df(temp_path)

res = {}

for path_file in df_path["path"]:
    df = pd.read_excel(path_file,sheet_name=None)
    # print(path_file)
    for key in df:
        if key not in res:
            res[key] = df[key]
        else:
            res[key] = pd.concat([res[key], df[key]])
        # print(key,res[key].shape)
    # break

with pd.ExcelWriter(join(temp_path, '統整.xlsx')) as writer:
    for key in res:
        res[key].to_excel(writer, sheet_name=key, index=False)