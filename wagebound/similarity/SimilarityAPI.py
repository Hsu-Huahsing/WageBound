# -*- coding: utf-8 -*-
"""
DGIS AccurateEstimation 測試呼叫腳本

原始功能：
    - 針對單一擔保品組出 payload
    - 呼叫 DGIS AccurateEstimation API
    - 取得 JSON 回傳結果

精簡重構：
    - 將 URL 與預設 payload 抽為常數
    - 包一層函式 call_accurate_estimation，方便未來重複呼叫或換參數
    - 改用 requests 模組標準命名，避免與 re(正規表示式) 混淆
"""

import requests
from typing import Any, Dict

# ----------------------------------------------------------------------
# 常數設定
# ----------------------------------------------------------------------
DGIS_URL = "http://dgisapiuat.ctbcbank.com/dgis/dgisapi/AccurateEstimation"

DEFAULT_PAYLOAD: Dict[str, Any] = {
    "SysType": "DGIS",
    "SubSysType": "01",
    "Account": "Z00002809",
    "Location": {
        "City": "006",
        "Town": "302",
        "Address": "",
        "OAddr": "",
        "CompareLV": "2",
        "X": 252814.544299987,
        "Y": 2745217.89140835,
        "FishID": 829466,
    },
    "RequestOption": {
        "IsFishIDUpdate": "Y",
        "IsHighRiskUpdate": "Y",
        "IsNegativeUpdate": "Y",
        "IsSectorCodeUpdate": "N",
        "IsAreaGradeFinalUpdate": "N",
    },
    "CollateralData": {
        "CollateralNo": "30201",
        "CaseNo": "20230802EI00023_0",
        "LoanPurpose": "01",
        "ProjectName": "昌益-音樂廳",
        "Builder": "",
        "Age": 21.0,
        "HouseType": "R2",
        "TotalFloor": "10",
        "FloorCode": "5",
        "FloorPublic": "0",
        "UseType": "01",
        "BuildingMaterial": "01",
        "BuildingReg": "01",
        "RoadWidth": 8.0,
        "UseArea": "00",
        "UseAreaTYPE": "F",
        "SurRoundings": "",
        "AnnouncementPrice": 33.06,
        "TotalFloorage": 50.27,
        "IndoorFloorage": 29.57,
        "ReCalFloorage": 42.27,
        "PublicFloorage": 12.70,
        "BasementFloorage": 0.0,
        "TerraceFloorage": 0.0,
        "LandArea": 9.88,
        "TotalPrice": 2100.0000,
        "ParkingSpaceTotalPrice": 100.0000,
        "ParkingSpaces": [
            {
                "ID": "1",
                "Type": "04",
                "Floor": "B2",
                "Area": 8.00,
            }
        ],
        "MainBuilding": 1,
        "BuildCommercialCnt": 0,
        "BuildHouseCommercialCnt": 0,
        "BuildHouseCnt": 1,
        "BuildIndustryCnt": 0,
        "BuildPublicCnt": 0,
        "isBasement": "N",
        "FloorOtherCnt": 1,
        "FloorFirstCnt": 1,
        "FloorTopCnt": 0,
        "FloorOverAllCnt": 0,
        "InCaseNo": "",
        "isBulkCase": "N",
        "BulkCaseNo": "",
        "BulkCasePhaseNo": "",
        "BulkCaseSection": "",
        "BulkCaseHousingNo": "",
        "BulkCaseHousingFloor": "5",
        "RefUnitPrice": 47.3149,
        "Fireinsurance": 380.0,
        "SectorCode": "0435",
        "AreaGradeFinal": "A",
        "CommunityNbr": "",
        "LatestAuditResultGap1year": "",
        "LatestPresumeUnit": -9999.0,
        "LatestLandPrice": -9999.0,
        "LatestStallAppraisePrice": -9999.0,
        "LatestTotalCurrentPrice": -9999.0,
        "AuditResultGapYear": -9999,
        "PolicyHpi": -9999.0,
    },
    "LegacyItem": {
        "Hierarchy": [],
        "Negative": [],
    },
}


# ----------------------------------------------------------------------
# 函式封裝
# ----------------------------------------------------------------------
def call_accurate_estimation(
    payload: Dict[str, Any] | None = None,
    url: str = DGIS_URL,
    timeout: int = 15,
) -> Dict[str, Any]:
    """
    呼叫 DGIS AccurateEstimation API，回傳 JSON 結果。

    Parameters
    ----------
    payload : dict, optional
        要送出的 payload，不給時使用 DEFAULT_PAYLOAD。
    url : str
        API endpoint。
    timeout : int
        requests 的 timeout 秒數。

    Returns
    -------
    dict
        API 回傳的 JSON 物件。

    Raises
    ------
    requests.HTTPError
        當 HTTP status code 非 2xx 時丟出。
    """
    if payload is None:
        payload = DEFAULT_PAYLOAD

    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()  # 非 2xx 會丟錯，方便除錯
    return resp.json()


# ----------------------------------------------------------------------
# 測試用 main
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 單筆測試呼叫
    response_json = call_accurate_estimation()
    # 你可以在這裡加上 print 或寫檔
    print(response_json)
