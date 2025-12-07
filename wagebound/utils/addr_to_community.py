# -*- coding: utf-8 -*-
import pandas as pd
import requests
from tqdm import tqdm

DGIS_URL = (
    "http://172.24.15.230/"
    "DGISAdressMatch/adressMatchApi/AdressMatchAreaName/AdressMatchAreaName"
)

SYSTEM_ID = "NUMS"
TRANS_NUM = "7108AF85-7EC5-48D8-9174-CEADD52E6F8B"
TRANS_DATE = "20231108"

INPUT_CSV = r"E:\車位自動化拆分專案\地址比對社區\地址比對清單.csv"
OUTPUT_XLSX = r"E:\車位自動化拆分專案\地址比對社區\outputfile\Case_CmUpdate2.xlsx"


def get_community(address: str, zip_code: str, session: requests.Session) -> dict:
    """呼叫內部 API 以地址＋郵遞區號查社區資訊，失敗時回傳空 dict。"""
    payload = {
        "SystemId": SYSTEM_ID,
        "TransNum": TRANS_NUM,
        "TransDate": TRANS_DATE,
        "ZipCode": str(zip_code),
        "LocationAdd": address,
    }

    try:
        resp = session.post(DGIS_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        # 出錯時回傳最小可用結構，避免整支程式中斷
        return {
            "CommunityNbr": None,
            "CommunityName": None,
            "Error": str(e),
        }

    # 預期正常會有 SystemId，但就算沒有也直接把 data 丟回去
    return data or {}


def main() -> None:
    df = pd.read_csv(INPUT_CSV, encoding="Big5")

    print(">> 開始比對...")
    building_keys = []
    community_names = []

    with requests.Session() as session:
        for row in tqdm(df.itertuples(index=False), total=len(df)):
            # 這裡假設欄位名稱為 add / Zip_Code
            out_json = get_community(
                address=getattr(row, "add"),
                zip_code=getattr(row, "Zip_Code"),
                session=session,
            )
            building_keys.append(out_json.get("CommunityNbr"))
            community_names.append(out_json.get("CommunityName"))

    # 一次性回寫欄位，避免在迴圈裡大量 df.loc
    df["DCDL_BuildingKey"] = building_keys
    df["DCDL_CollateralName"] = community_names
    # 若不希望輸出 index，建議關掉
    df.to_excel(OUTPUT_XLSX, index=False)

    print(">> 完成比對與輸出!!!")


if __name__ == "__main__":
    main()
