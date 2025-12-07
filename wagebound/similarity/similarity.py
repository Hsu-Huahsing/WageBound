from datetime import datetime

# ----------------------------------------------------------------------
# 共用小工具
# ----------------------------------------------------------------------

def score_by_threshold(value, rules):
    """
    通用門檻給分：
        rules 形式：[[threshold1, score1], [threshold2, score2], ...]
        回傳第一個 value <= threshold 的 score，否則 0
    """
    for threshold, score in rules:
        if value <= threshold:
            return score
    return 0


def is_digit_like(x) -> bool:
    """簡單檢查是否為純數字字串."""
    return isinstance(x, (int, float)) or (isinstance(x, str) and x.isdigit())


# ----------------------------------------------------------------------
# 0 排除比對案件的規則
# ----------------------------------------------------------------------
def case_ingore(self, CollateralInfo, NearCase):
    """判斷是否排除該比對案件（Y=排除, N=保留）"""

    # 1. 建物類型不同
    if NearCase["HouseTypeCode"] != CollateralInfo["HouseType_decode"]:
        return "Y"

    # 2. 異常交易
    if NearCase["OutlierTxn"] == "Y":
        return "Y"

    # 3. 地下樓層
    floor_code_str = str(NearCase["FloorCode"])
    if "B" in floor_code_str:
        return "Y"

    try:
        floor_code_int = int(floor_code_str)
    except ValueError:
        return "Y"

    if floor_code_int < 1:
        return "Y"

    # 4. 擔保品不在一樓時，不選一樓案件
    if int(CollateralInfo["FloorCode"]) != 1 and floor_code_int == 1:
        return "Y"

    return "N"


# ----------------------------------------------------------------------
# 1. 交易期間
# ----------------------------------------------------------------------
def score1_transaction_datediff(self, CollateralInfo, NearCase, similarityDict):
    time_diff_month = NearCase["TimeDiffOfMonth"]
    rules = similarityDict["DealMonthDiff"]  # [[6, 62], [12, 60], [24, 55], ...]
    return score_by_threshold(time_diff_month, rules)


# ----------------------------------------------------------------------
# 2. 案件距離
# ----------------------------------------------------------------------
def score2_distance(self, CollateralInfo, NearCase, similarityDict):
    distance = NearCase["Distance"]

    if CollateralInfo["HouseType"] == "R1":
        rules = similarityDict["Distance"]       # R1 用 Distance
    else:
        rules = similarityDict["Distance_R2"]    # 其他用 Distance_R2

    return score_by_threshold(distance, rules)


# ----------------------------------------------------------------------
# 3. 社區 / 巷弄比較
# ----------------------------------------------------------------------
def score3_community_or_alley(self, CollateralInfo, NearCase, similarityDict):
    """
    R1: 用 addressNearLevel + Alley 規則
    非 R1: 同社區給分
    """
    house_type = CollateralInfo["HouseType"]

    if house_type == "R1":
        level = NearCase["addressNearLevel"]
        alley_rules = similarityDict["Alley"]  # [[[3, 5000], 12], [2, 9], [1, 8], [0, 0]]

        # alley_rules[0][0] = [3, 5000] → 這裡只用等號比對 level
        if level == alley_rules[0][0][0]:
            return alley_rules[0][1]
        elif level == alley_rules[1][0]:
            return alley_rules[1][1]
        elif level == alley_rules[2][0]:
            return alley_rules[2][1]
        else:
            return alley_rules[3][1]

    # 非 R1 → 看 Community
    if NearCase["CommunityNbr"] == CollateralInfo["CommunityNbr"] and NearCase["CommunityNbr"]:
        return similarityDict["Community"][0][1]  # 同社區
    return 0


# ----------------------------------------------------------------------
# 4. 樓層位置
# ----------------------------------------------------------------------
def score4_floor(self, CollateralInfo, NearCase, similarityDict):
    house_type = CollateralInfo["HouseType"]

    try:
        collateral_floor = int(CollateralInfo["FloorCode"])
        collateral_total_floor = int(CollateralInfo["TotalFloor"])
        near_floor = int(NearCase["FloorCode"])
        near_total_floor = int(NearCase["TotalFloorCode"])
    except (TypeError, ValueError):
        return 0

    # 非 R1：用樓層差距計分
    if house_type != "R1" and collateral_floor not in (998, 999) and near_floor not in (998, 999):
        floor_diff = abs(near_floor - collateral_floor)
        rules = similarityDict["Floor_R2"]  # [[3, 3], [8, 1]]
        return score_by_threshold(floor_diff, rules)

    # R1：同樓層 or 同為「其他樓」
    if house_type == "R1":
        # 同樓層
        if near_floor == collateral_floor and collateral_floor not in (998, 999):
            return similarityDict["Floor"][0][1]

        # 同為「其他樓」（既不是 1 樓，也不是頂樓 / 特殊碼）
        if (
            collateral_floor not in (1, 998, 999)
            and collateral_total_floor != collateral_floor
            and near_total_floor != near_floor
            and near_floor not in (1, 998, 999)
            and near_floor > 0
        ):
            return similarityDict["Floor"][1][1]

    return 0


# ----------------------------------------------------------------------
# 5. 坪數差異
# ----------------------------------------------------------------------
def score5_area(self, CollateralInfo, NearCase, similarityDict):
    collateral_area = CollateralInfo["ReCalFloorage"]

    if collateral_area in (0, None):
        return 0

    area_diff_pct = abs(NearCase["BuildingArea"] - collateral_area) / collateral_area
    rules = similarityDict["Ping"]  # [[0.3, 2], [0.5, 1]]
    return score_by_threshold(area_diff_pct, rules)


# ----------------------------------------------------------------------
# 6. 屋齡比較
# ----------------------------------------------------------------------
def score6_age(self, CollateralInfo, NearCase, similarityDict):
    collateral_age = CollateralInfo["Age"]
    age_diff = abs(NearCase["Age"] - collateral_age)

    if CollateralInfo["HouseType"] == "R1":
        rules = similarityDict["Age"]
    else:
        rules = similarityDict["Age_R2"]

    return score_by_threshold(age_diff, rules)


# ----------------------------------------------------------------------
# 7. 巷弄屬性（目前未在 similarity_caculate 使用）
# ----------------------------------------------------------------------
def score7_alley(self, CollateralInfo, NearCase, similarityDict):
    """
    巷弄屬性 + 距離組合。
    注意：原始程式第三個條件重複，這裡修正為 level == Alley[2][0]。
    """
    level = NearCase["addressNearLevel"]
    distance = NearCase["Distance"]
    alley_rules = similarityDict["Alley"]  # [[[3, 5000], 12], [2, 9], [1, 8], [0, 0]]

    if level == alley_rules[0][0][0] and distance <= alley_rules[0][0][1]:
        # 同巷弄屬性、同路段、距離<=指定值
        return alley_rules[0][1]
    elif level == alley_rules[1][0]:
        return alley_rules[1][1]
    elif level == alley_rules[2][0]:
        return alley_rules[2][1]
    else:
        return alley_rules[3][1]


# ----------------------------------------------------------------------
# 業務層：相似度計算
# ----------------------------------------------------------------------
def similarity_caculate(self, NearCase, similarityDict):
    # 1. 查詢擔保品資訊
    collateral_info = self.dfCollateral[self.dfCollateral["ApplNo"] == NearCase["ApplNo"]].iloc[0]

    # 2. 排除條件
    ignore_flag = self.case_ingore(collateral_info, NearCase)

    # 3. 六大構面得分
    s1 = self.score1_transaction_datediff(collateral_info, NearCase, similarityDict)
    s2 = self.score2_distance(collateral_info, NearCase, similarityDict)
    s3 = self.score3_community_or_alley(collateral_info, NearCase, similarityDict)
    s4 = self.score4_floor(collateral_info, NearCase, similarityDict)
    s5 = self.score5_area(collateral_info, NearCase, similarityDict)
    s6 = self.score6_age(collateral_info, NearCase, similarityDict)

    return [ignore_flag, s1, s2, s3, s4, s5, s6]


def floorMappingAndCheckDigit(self, x):
    mapped = self.TotalFloorMapping.get(x, x)
    return int(mapped) if is_digit_like(mapped) else 9999


# ----------------------------------------------------------------------
# 參數與計算流程
# ----------------------------------------------------------------------
scoreParameter_v2 = {
    "DealMonthDiff": [[6, 62], [12, 60], [24, 55]],
    "Distance": [[200, 7], [500, 4], [1000, 1]],
    "Alley": [[[3, 5000], 12], [2, 9], [1, 8], [0, 0]],
    "Floor": [["same", 3], ["other", 1]],
    "Ping": [[0.3, 2], [0.5, 1]],
    "Age": [[3, 10], [5, 5], [10, 1]],
    "Distance_R2": [[100, 15], [500, 10], [1000, 5]],
    "Community": [["same", 4], ["similar", 3]],
    "Alley_R2": [[[3, 5000], 11], [2, 9], [1, 8], [0, 0]],
    "Floor_R2": [[3, 3], [8, 1]],
    "Age_R2": [[3, 10], [5, 5], [10, 2]],
}

version_int = "2"
use_score_parameter = scoreParameter_v2

dfCompareCases_caculate = dfCompareCases.copy()

print("computing...")
dfCompareCases_caculate[f"v{version_int}_result"] = dfCompareCases_caculate.apply(
    lambda row: dgis.similarity_caculate(row, use_score_parameter), axis=1
)

print("summarizing...")
# 把 list 展開成獨立欄位，比逐一 .apply(x[0]) 乾淨很多
result_cols = [
    f"v{version_int}_ignore",
    f"v{version_int}_s1_deal_datediff",
    f"v{version_int}_s2_distance",
    f"v{version_int}_s3_community_or_alley",
    f"v{version_int}_s4_floor",
    f"v{version_int}_s5_area",
    f"v{version_int}_s6_age",
]

dfCompareCases_caculate[result_cols] = pd.DataFrame(
    dfCompareCases_caculate[f"v{version_int}_result"].tolist(),
    index=dfCompareCases_caculate.index,
)

# 總分：六個構面分數加總
score_cols = result_cols[1:]  # 除了 ignore 以外
dfCompareCases_caculate[f"v{version_int}_similarity"] = dfCompareCases_caculate[
    score_cols
].sum(axis=1)

print("sorting...")
dfCompareCases_caculate = dfCompareCases_caculate.sort_values(
    ["ApplNo", f"v{version_int}_similarity"], ascending=False
).reset_index(drop=True)

dfCompareCases_caculate.head()
datetime.now()
