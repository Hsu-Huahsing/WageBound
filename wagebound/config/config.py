# -*- coding: utf-8 -*-
"""
DGIS 專案通用設定與工具函式
Created on Thu Oct 19 17:17:15 2023
@author: Z00051711
"""

from __future__ import annotations

from typing import Dict, List, Mapping, MutableMapping, Optional, Any


# ============================================================================
# 路徑設定
# ============================================================================

path_dic: Dict[str, str] = {
    "DGIS": r"D:\DGIS\專案",
}


# ============================================================================
# 原始欄位名稱 → 統一英文欄位名稱
# ============================================================================

colname: Dict[str, Dict[str, str]] = {
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

dropcol: Dict[str, List[str]] = {
    "不動產買賣": ["主建物面積", "附屬建物面積", "陽台面積", "電梯"],
}


# ============================================================================
# 行政區代碼與名稱
# ============================================================================

cityname: Dict[str, str] = {
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

cityname_change: Dict[str, str] = {
    "桃園縣": "桃園市",
    "台中縣": "台中市",
    "高雄縣": "高雄市",
    "台南縣": "台南市",
    # "新竹縣": "新竹市",
}


# ============================================================================
# DGIS → DRPD 欄位對照
# ============================================================================

dgiskey: Dict[str, str] = {
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
    "Note": "DRPD_Note",
    "Number": "DRPD_Number",
    "FishID": "DRPD_FishId",
    "zip": "DRPD_ZipCode",
}

dgiskey_lis: List[str] = [
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


# ============================================================================
# 相似度等級設定（停車位比價用）
# ============================================================================

similarityLV: Dict[str, range] = {
    "L1": range(90, 101),
    "L2": range(85, 90),
    "L3": range(75, 85),
    "L4": range(70, 75),
    "L5": range(65, 70),
}

similarityLV_new: Dict[str, range] = {
    "L1": range(95, 101),
    "L2": range(90, 95),
    "L3": range(85, 90),
    "L4": range(80, 85),
    "L5": range(75, 80),
    "L6": range(70, 75),
    "L7": range(65, 70),
}

SIMILARITY_THRESHOLD: int = 65  # 小於此分數的案件不列入相似案例


def similarityLV_name(
    similarity_int: int,
    sim_dict: Optional[Mapping[str, range]] = None,
    typ: str = "text",
) -> Optional[Any]:
    """
    將相似度分數轉成等級名稱或數字等級。

    Parameters
    ----------
    similarity_int : int
        相似度分數（0~100）
    sim_dict : Mapping[str, range], optional
        使用哪一套等級表，預設用 similarityLV
    typ : {"text", "num"}
        text → 回傳 'L1' / 'L2'
        num  → 回傳 1 / 2

    Returns
    -------
    str | int | None
    """
    if sim_dict is None:
        sim_dict = similarityLV

    for key, rg in sim_dict.items():
        if similarity_int in rg:
            if typ == "text":
                return key
            if typ == "num":
                return int(key.replace("L", ""))
    return None


def comparecase_clean(
    dic_lis: Optional[Mapping[str, List[MutableMapping[str, Any]]]] = None,
    AppNbr: str = "",
    CollNbr: str = "",
) -> Dict[str, List[Dict[str, Any]]]:
    """
    將 comparecase 回傳結果整理成統一格式。

    傳入的 dic_lis 結構：
        {
            'LVR': [
                {
                    'properties': {
                        'Similarity': 90,
                        ...
                    },
                    ...
                },
                ...
            ],
            'CTBC_Inside': [...],
        }

    回傳：
        每一筆 feature 取出 properties，增加：
            - SimilarityName / SimilarityVal      （舊等級）
            - SimilarityName_new / SimilarityVal_new（新等級）
            - ApplicationNbr / CollateralNo
        並過濾掉 Similarity < SIMILARITY_THRESHOLD 的案件。
    """
    if dic_lis is None:
        dic_lis = {}

    dic_new: Dict[str, List[Dict[str, Any]]] = {}

    for source, features in dic_lis.items():
        cleaned_list: List[Dict[str, Any]] = []

        for item in features:
            props = item.get("properties", {})
            score = props.get("Similarity")
            if score is None or score < SIMILARITY_THRESHOLD:
                # 相似分太低，直接略過
                continue

            # 直接在原 props 上增加欄位
            props["SimilarityName"] = similarityLV_name(score, similarityLV, typ="text")
            props["SimilarityVal"] = similarityLV_name(score, similarityLV, typ="num")
            props["SimilarityName_new"] = similarityLV_name(score, similarityLV_new, typ="text")
            props["SimilarityVal_new"] = similarityLV_name(score, similarityLV_new, typ="num")
            props["ApplicationNbr"] = AppNbr
            props["CollateralNo"] = CollNbr

            cleaned_list.append(props)

        dic_new[source] = cleaned_list

    return dic_new


def comparecase_select(
    comparecase: Optional[List[MutableMapping[str, Any]]] = None,
    select_lis: Optional[List[str]] = None,
) -> Dict[str, List[MutableMapping[str, Any]]]:
    """
    從 comparecase 結果中，挑出指定 CaseType 的 features。

    Parameters
    ----------
    comparecase : list[dict]
        每一筆元素結構：
            {
                'CaseType': 'LVR' 或 'CTBC_Inside',
                'FeatureData': {
                    'features': [...],
                    ...
                }
            }
    select_lis : list[str], optional
        要保留的 CaseType 清單，預設為 ['LVR', 'CTBC_Inside']

    Returns
    -------
    dict[str, list[dict]]
        { CaseType: features_list }
    """
    if comparecase is None:
        comparecase = []
    if select_lis is None:
        select_lis = ["LVR", "CTBC_Inside"]

    res: Dict[str, List[MutableMapping[str, Any]]] = {}
    for dic in comparecase:
        case_type = dic.get("CaseType")
        if case_type in select_lis:
            features = dic.get("FeatureData", {}).get("features", [])
            res[case_type] = features
    return res


# ============================================================================
# 建築成本區間（各縣市建坪造價切分）
# ============================================================================

build_cost: Dict[str, Dict[str, range]] = {
    "台北市": {
        "seg1_price": range(0, 50),
        "seg2_price": range(50, 75),
        "seg3_price": range(75, 100),
        "seg4_price": range(100, 125),
        "seg5_price": range(125, 150),
        "seg6_price": range(125, 150),
        "seg7_price": range(150, 180),
        "seg8_price": range(180, 210),
        "seg9_price": range(210, 999),
    },
    "新北市": {
        "seg1_price": range(0, 20),
        "seg2_price": range(20, 30),
        "seg3_price": range(30, 50),
        "seg4_price": range(50, 70),
        "seg5_price": range(70, 999),
    },
    "桃園市": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 20),
        "seg3_price": range(20, 30),
        "seg4_price": range(30, 40),
        "seg5_price": range(40, 50),
        "seg6_price": range(50, 999),
    },
    "台中市": {
        "seg1_price": range(0, 20),
        "seg2_price": range(20, 25),
        "seg3_price": range(25, 30),
        "seg4_price": range(30, 40),
        "seg5_price": range(40, 50),
        "seg6_price": range(50, 999),
    },
    "台南市": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 30),
        "seg5_price": range(30, 40),
        "seg6_price": range(40, 50),
        "seg7_price": range(50, 999),
    },
    "高雄市": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 25),
        "seg5_price": range(25, 30),
        "seg6_price": range(30, 40),
        "seg7_price": range(40, 50),
        "seg8_price": range(50, 70),
        "seg9_price": range(70, 999),
    },
    "宜蘭縣": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 30),
        "seg4_price": range(30, 40),
        "seg5_price": range(40, 50),
        "seg6_price": range(50, 999),
    },
    "新竹縣": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 20),
        "seg3_price": range(20, 30),
        "seg4_price": range(30, 40),
        "seg5_price": range(40, 50),
        "seg6_price": range(50, 999),
    },
    "新竹市": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 20),
        "seg3_price": range(20, 30),
        "seg4_price": range(30, 40),
        "seg5_price": range(40, 50),
        "seg6_price": range(50, 999),
    },
    "苗栗縣": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 30),
        "seg4_price": range(30, 999),
    },
    "彰化縣": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 30),
        "seg4_price": range(30, 40),
        "seg5_price": range(40, 50),
        "seg6_price": range(50, 999),
    },
    "南投縣": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 30),
        "seg4_price": range(30, 999),
    },
    "雲林縣": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 30),
        "seg5_price": range(30, 40),
        "seg6_price": range(40, 999),
    },
    "嘉義縣": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 30),
        "seg5_price": range(30, 40),
        "seg6_price": range(40, 999),
    },
    "嘉義市": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 30),
        "seg5_price": range(30, 40),
        "seg6_price": range(40, 999),
    },
    "屏東縣": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 25),
        "seg5_price": range(25, 30),
        "seg6_price": range(30, 40),
        "seg7_price": range(40, 50),
        "seg8_price": range(50, 999),
    },
    "台東縣": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 25),
        "seg5_price": range(25, 30),
        "seg6_price": range(30, 40),
        "seg7_price": range(40, 50),
        "seg8_price": range(50, 999),
    },
    "花蓮縣": {
        "seg1_price": range(0, 10),
        "seg2_price": range(10, 15),
        "seg3_price": range(15, 20),
        "seg4_price": range(20, 25),
        "seg5_price": range(25, 30),
        "seg6_price": range(30, 40),
        "seg7_price": range(40, 50),
        "seg8_price": range(50, 999),
    },
    "澎湖縣": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 25),
        "seg4_price": range(25, 999),
    },
    "基隆市": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 25),
        "seg4_price": range(25, 30),
        "seg5_price": range(30, 999),
    },
    "金門縣": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 25),
        "seg4_price": range(25, 999),
    },
    "連江縣": {
        "seg1_price": range(0, 15),
        "seg2_price": range(15, 20),
        "seg3_price": range(20, 25),
        "seg4_price": range(25, 999),
    },
}

seg_price_num: Dict[str, int] = {
    "seg1_price": 1,
    "seg2_price": 2,
    "seg3_price": 3,
    "seg4_price": 4,
    "seg5_price": 5,
    "seg6_price": 6,
    "seg7_price": 7,
    "seg8_price": 8,
    "seg9_price": 9,
}


# ============================================================================
# 主建材對照（實價 → CTBC 分類）
# ============================================================================

ctbc_mainmaterial_ref: Dict[int, int] = {
    5: 2,
    6: 2,
    7: 2,
    8: 2,
    9: 2,
    10: 1,
    11: 1,
    12: 1,
    13: 2,
    14: 2,
    15: 2,
    16: 2,
    17: 2,
    18: 1,
    19: 2,
    20: 2,
    21: 2,
    22: 2,
}

ctbc_mainmaterial_ref_temp: Dict[int, int] = {
    3: 1,
    4: 1,
}


# ============================================================================
# 數值區間切分（屋齡 / 面積 / 單價等）
# ============================================================================

checkinterval: Dict[str, range] = {
    "00.-9999999999~0": range(-10000000000, 0),
    "01.0~9": range(0, 10),
    "02.10~19": range(10, 20),
    "03.20~29": range(20, 30),
    "04.30~39": range(30, 40),
    "05.40~49": range(40, 50),
    "06.50~59": range(50, 60),
    "07.60~69": range(60, 70),
    "08.70~79": range(70, 80),
    "09.80~89": range(80, 90),
    "10.90~99": range(90, 100),
    "11.100~149": range(100, 150),
    "12.150~199": range(150, 200),
    "13.200~249": range(200, 250),
    "14.250~299": range(250, 300),
    "15.300~399": range(300, 400),
    "16.400~499": range(400, 500),
    "17.500~749": range(500, 750),
    "18.750~999": range(750, 1000),
    "19.1000~9999999999": range(1000, 10000000000),
}


# ============================================================================
# 欄位長度檢查設定
# ============================================================================

maxlength: Dict[str, int] = {
    "DRPD_Address": 100,
    "DRPD_BuildingType": 50,
    "DRPD_BuildingTypeFlag": 2,
    "DRPD_City": 20,
    "DRPD_District": 20,
    "DRPD_LandUseType": 2,
    "DRPD_ZipCode": 3,
    "DRPD_TradeTarget": 20,
    "DRPD_NonUrbanDistrict": 10,
    "DRPD_NonUrbanland": 10,
    "DRPD_Transactions": 50,
    "DRPD_TransFloor": 100,
    "DRPD_TotalFloor": 50,
    "DRPD_MainPurpose": 50,
    "DRPD_MainMaterial": 50,
    "DRPD_Partition": 1,
    "DRPD_Management": 1,
    "DRPD_RealEstateStallFlag": 60,
    "DRPD_HasNote": 1,
    "DRPD_Note": 300,
    "DRPD_SpecialTradeFlag": 50,
    "DRPD_Number": 20,
    "DRPD_BuildingSeg": 2,
    "DRPD_ModifyFlag": 1,
    "DRPD_BuildingName": 50,
    "DRPD_BuildingKey": 30,
    "DRPD_NoteFlag": 999,
    "DRPD_OutlierTxn": 1,
    "DRPD_RoadSecName": 20,
    "DRPD_AlleyName": 20,
    "DRPD_IsAlley": 1,
    "DRPD_CommunityFlag": 20,
}


# ============================================================================
# 其他欄位清理用名稱對照
# ============================================================================

clean_colname: Dict[str, str] = {
    "CTBCCommunityPlaneStallPriceCounts": "CTBCCommunity_P_Stall_Counts",
    "CTBCCommunityPlaneStallPriceP50": "CTBCCommunity_P_Stall_P50",
    "CTBCCommunityMechanicalStallPriceCounts": "CTBCCommunity_M_Stall_Counts",
    "CTBCCommunityMechanicalStallPriceP50": "CTBCCommunity_M_Stall_P50",
    "ActualSimulairtyPlaneStallPriceCounts": "ActualSimulairty_P_Stall_Counts",
    "ActualSimulairtyPlaneStallPriceP50": "ActualSimulairty_P_Stall_P50",
    "ActualSimulairtyPlaneStallPriceMin": "ActualSimulairty_P_Stall_min",
    "ActualSimulairtyPlaneStallPriceMax": "ActualSimulairty_P_Stall_max",
    "ActualSimulairtyMechanicalStallPriceCounts": "ActualSimulairty_M_Stall_Counts",
    "ActualSimulairtyMechanicalStallPriceP50": "ActualSimulairty_M_Stall_P50",
    "ActualSimulairtyMechanicalStallPriceMin": "ActualSimulairty_M_Stall_min",
    "ActualSimulairtyMechanicalStallPriceMax": "ActualSimulairty_M_Stall_max",
    "ActuralPlaneStallPriceCountsV2": "Actural_P_Stall_CountsV2",
    "ActuralPlaneStallPriceP50V2": "Actural_P_Stall_P50V2",
    "ActuralPlaneStallPriceP5V2": "Actural_P_Stall_P5V2",
    "ActuralPlaneStallPriceP95V2": "Actural_P_Stall_P95V2",
    "ActuralMechanicalStallPriceCountsV2": "Actural_M_Stall_CountsV2",
    "ActuralMechanicalStallPriceP50V2": "Actural_M_Stall_P50V2",
    "ActuralMechanicalStallPriceP5V2": "Actural_M_Stall_P5V2",
    "ActuralMechanicalStallPriceP95V2": "Actural_M_Stall_P95V2",
    "SimilarityFlag": "Similarityflag",
}


__all__ = [
    "path_dic",
    "colname",
    "dropcol",
    "cityname",
    "cityname_change",
    "dgiskey",
    "dgiskey_lis",
    "similarityLV",
    "similarityLV_new",
    "SIMILARITY_THRESHOLD",
    "similarityLV_name",
    "comparecase_clean",
    "comparecase_select",
    "build_cost",
    "seg_price_num",
    "ctbc_mainmaterial_ref",
    "ctbc_mainmaterial_ref_temp",
    "checkinterval",
    "maxlength",
    "clean_colname",
]
