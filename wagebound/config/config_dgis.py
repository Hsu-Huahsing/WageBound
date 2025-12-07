# -*- coding: utf-8 -*-
"""
DGIS 實價登錄清理用設定檔
"""

from os.path import join

# -------------------------------
# 路徑與檔名設定
# -------------------------------

DGIS_RAW_ROOT = r"D:\DGIS\原始資料"
DGIS_WB_ROOT = r"D:\DGIS\workbench"

# 月份區間設定
DATE_START = "2021-04"   # 第一個月份
DATE_PERIODS = 38        # 月數（MS = Month Start）

# 參考檔路徑
PATH_XY = r"C:\Users\z00188600\Desktop\DGIS移轉\FishID.xlsx"
PATH_ZIP = r"D:\Users\z00188600\AppData\Local\anaconda3\Lib\site-packages\ctbc_project\ZIP.xlsx"

# 主要輸出檔名
FILE_TOTAL = "GEOM_CTBC_RealPriceDetail.csv"
FILE_SEND = "GEOM_CTBC_RealPriceDetail_send.csv"

# 原始實價登錄 Excel 副檔名
EXCEL_EXT = ".xls"

# -------------------------------
# 欄位 mapping
# -------------------------------

COLNAME = {
    "建物": {
        "編號": "Number",
        "主要用途": "Building_Main_Use",
        "主要建材": "Building_Main_Material",
        "建物移轉總面積(平方公尺)": "Trans_Area",
        "屋齡": "Building_Age",
        "建物移轉面積(平方公尺)": "Building_Trans_Area",
        "建物移轉面積平方公尺": "Building_Trans_Area",
        "建物完成日期": "Building_Completion_Date",
        "建築完成日期": "Building_Completion_Date",
        "總層數": "Building_Total_Floor",
        "建物分層": "Building_layer",
    },
    "不動產買賣": {
        "行政區": "City",
        "鄉鎮市區": "District",
        "交易標的": "Trading_Target",
        "土地區段位置/建物區段門牌": "Address",
        "土地區段位置/建物門牌": "Address",
        "土地位置/建物門牌": "Address",
        "土地移轉總面積(平方公尺)": "Land_Trans_Area",
        "都市土地使用分區": "Land_use_Type",
        "非都市土地使用分區": "Non_urban_District",
        "非都市土地使用編定": "Non_urban_Land",
        "交易年月日": "Trading_Date",
        "交易筆棟數": "Transactions",
        "移轉層次": "Trans_Floor",
        "總樓層數": "Total_Floor",
        "建物型態": "Building_Type",
        "主要用途": "Main_Use",
        "主要建材": "Main_Material",
        "建築完成年月": "Completion_Date",
        "建物移轉總面積(平方公尺)": "Trans_Area",
        "建物現況格局-房": "Layout_Bedroom",
        "建物現況格局-廳": "Layout_Livroom",
        "建物現況格局-衛": "Layout_Bathroom",
        "建物現況格局-隔間": "Partition_YN",
        "有無管理組織": "Management_YN",
        "總價(元)": "Total_Price",
        "單價(元/平方公尺)": "Unit_Price",
        "車位類別": "Stall_Type",
        "車位移轉總面積(平方公尺)": "Stall_trans_area",
        "車位總價(元)": "Stall_Total_Price",
        "交易標的橫坐標": "Trading_Target_X",
        "交易標的縱坐標": "Trading_Target_Y",
        "有無備註欄(Y/N)": "Note_YN",
        "備註": "Note",
        "編號": "Number",
        "屋齡": "Building_Age",
        "建物移轉面積(平方公尺)": "Building_Trans_Area",
        "總層數": "Building_Total_Floor",
        "建物分層": "Building_layer",
    },
}

DROPCOL = {
    "不動產買賣": [
        "主建物面積",
        "附屬建物面積",
        "陽台面積",
        "電梯",
    ]
}

CITYNAME = {
    "A": "台北市",
    "B": "台中市",
    "C": "基隆市",
    "D": "台南市",
    "E": "高雄市",
    "F": "新北市",
    "G": "宜蘭縣",
    "H": "桃園市",
    "I": "嘉義市",
    "J": "新竹縣",
    "K": "苗栗縣",
    "M": "南投縣",
    "N": "彰化縣",
    "O": "新竹市",
    "P": "雲林縣",
    "Q": "嘉義縣",
    "T": "屏東縣",
    "U": "花蓮縣",
    "V": "台東縣",
    "W": "金門縣",
    "X": "澎湖縣",
    "Z": "連江縣",
}

DGISKEY = {
    "City": "DRPD_City",
    "District": "DRPD_District",
    "Trading_Target": "DRPD_TradeTarget",
    "Address": "DRPD_Address",
    "Land_Trans_Area": "DRPD_LandTransArea",
    "Land_use_Type": "DRPD_LandUseType",
    "Non_urban_District": "DRPD_NonUrbanDistrict",
    "Non_urban_Land": "DRPD_NonUrbanland",
    "Trading_Date": "DRPD_TradeDate",
    "Transactions": "DRPD_Transactions",
    "Trans_Floor": "DRPD_TransFloor",
    "Total_Floor": "DRPD_TotalFloor",
    "Building_Type": "DRPD_BuildingType",
    "Main_Use": "DRPD_MainPurpose",
    "Main_Material": "DRPD_MainMaterial",
    "Completion_Date": "DRPD_CompletionDate",
    "Trans_Area": "DRPD_TransArea",
    "Layout_Bedroom": "DRPD_LayoutBedroom",
    "Layout_Livroom": "DRPD_LayoutLivroom",
    "Layout_Bathroom": "DRPD_LayoutBathroom",
    "Total_Price": "DRPD_TotalPrice",
    "Unit_Price": "DRPD_UnitPrice",
    "Note": "DRPD_Note",
    "Number": "DRPD_Number",
    "FishID": "DRPD_FishId",
    "zip": "DRPD_ZipCode",
}

DGISKEY_LIST = [
    "DRPD_Sequence",
    "Geom",
    "DRPD_ZipCode",
    "DRPD_City",
    "DRPD_District",
    "DRPD_TradeTarget",
    "DRPD_Address",
    "DRPD_LandTransArea",
    "DRPD_LandUseType",
    "DRPD_NonUrbanDistrict",
    "DRPD_NonUrbanland",
    "DRPD_TradeDate",
    "DRPD_Transactions",
    "DRPD_TransFloor",
    "DRPD_TotalFloor",
    "DRPD_BuildingType",
    "DRPD_BuildingTypeFlag",
    "DRPD_MainPurpose",
    "DRPD_MainMaterial",
    "DRPD_CompletionDate",
    "DRPD_TransArea",
    "DRPD_LayoutBedroom",
    "DRPD_LayoutLivroom",
    "DRPD_LayoutBathroom",
    "DRPD_Partition",
    "DRPD_Management",
    "DRPD_TotalPrice",
    "DRPD_UnitPrice",
    "DRPD_TargetX",
    "DRPD_TargetY",
    "DRPD_HasNote",
    "DRPD_Note",
    "DRPD_Number",
    "DRPD_BuildingSeg",
    "DRPD_BuildingAge",
]
