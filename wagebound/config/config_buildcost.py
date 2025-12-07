# -*- coding: utf-8 -*-
"""
建築成本 × 透天房地分離：建模用參數設定
"""

from datetime import datetime

# --------- 基本參數 ---------

# 分組統計最低樣本數（適用於 zip / floor / area 等粗細層級）
MIN_GROUP_COUNT = 30

# 特殊區域（價格地板不同）
SPECIAL_REGIONS = {"台中市", "南投縣", "彰化縣"}

# 建模時間窗設定
START_DATE_STR = "2025-04-01"   # 起算月份
AP_WINDOW_MONTHS = 6            # 市場成交資料：取 N 個月內
CTBC_MONTHS = 6                 # CTBC 案件：取 N 個月申請書號年月

# Var（倍數）與 Var2（金額）離散化刻度
VAR_STEP = 0.2   # Var 四捨五入刻度
VAR2_STEP = 0.5  # Var2 四捨五入刻度

# 特殊區域與一般區域的「最低價格地板」設定（單位：萬元）
SPECIAL_MIN_PRICE = {
    "new": 3.0,   # remaining_year > 0 or between(-3,0)
    "mid": 2.5,   # remaining_year between(-9,-4)
    "long": 1.5,  # remaining_year <= -10
}

GENERAL_MIN_PRICE = {
    "new": 1.0,
    "mid": 0.8,
    "long": 0.5,
}

# --------- 路徑設定 ---------

# 策略系統變數表
PATH_VARTABLE = r"E:\數位專案\HPM2.0\2025-11RC\策略系統參數表彙整_20250528.xlsx"

# 建築工程總指數
PATH_BUILDINDEX = r"E:\數位專案\HPM2.0\2025-11RC\建築工程總指數251030.xlsx"

# DGIS 實價成交明細
PATH_AP = r"D:\DGIS\workbench\202510\上傳DGIS\GEOM_CTBC_RealPriceDetail.csv"

# 房地分離土地拆分區資料夾
PATH_LANDSPLIT = r"E:\數位專案\HPM2.0\2025-11RC"

# --------- 群組層級設定（方便之後調整） ---------

GROUP_LEVELS = {
    "level1": ["Area_Nbr", "total_floor_flag", "Building_Age_flag2"],
    "level2": ["Area_Nbr", "Building_Age_flag2"],
    "level3": ["Area_Nbr"],
    "level4": ["County"],
}
