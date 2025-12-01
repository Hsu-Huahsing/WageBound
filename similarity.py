# 0 排除比對案件的規則
def case_ingore(self, CollateralInfo, NearCase):
    if NearCase['HouseTypeCode'] != CollateralInfo['HouseType_decode']:  # 排除不同建物類型
        return 'Y'
    elif NearCase['OutlierTxn'] == 'Y':  # 排除異常交易
        return 'Y'
    elif 'B' in str(NearCase['FloorCode']):  # 排除地下
        return 'Y'
    elif int(NearCase['FloorCode']) < 1:  # 排除地下
        return 'Y'
    elif int(CollateralInfo['FloorCode']) != 1 and int(NearCase['FloorCode']) == 1:  # 擔保品在1樓，不選1樓案件
        return 'Y'
    else:
        return 'N'  # 確認要比對的案件


# 規則1 比對交易期間
def score1_transaction_datediff(self, CollateralInfo, NearCase, similarityDict):

    TimeDiffOfMonth = NearCase['TimeDiffOfMonth']
    
    if TimeDiffOfMonth <= similarityDict['DealMonthDiff'][0][0]:  # 近半年
        return similarityDict['DealMonthDiff'][0][1]
    elif TimeDiffOfMonth <= similarityDict['DealMonthDiff'][1][0]:  # 近一年
        return similarityDict['DealMonthDiff'][1][1]
    elif TimeDiffOfMonth <= similarityDict['DealMonthDiff'][2][0]:  # 近兩年
        return similarityDict['DealMonthDiff'][2][1]
    elif TimeDiffOfMonth <= similarityDict['DealMonthDiff'][3][0]:  # 近兩年
        return similarityDict['DealMonthDiff'][3][1]
    else:  # 兩年以上
        return 0


# 2 案件距離
def score2_distance(self, CollateralInfo, NearCase, similarityDict):

    Distance = NearCase['Distance']
    Distance_R2 = NearCase['Distance']
    
    if CollateralInfo['HouseType'] == 'R1':
        if Distance <= similarityDict['Distance'][0][0]:  # 200公尺內
            return similarityDict['Distance'][0][1]
        elif Distance <= similarityDict['Distance'][1][0]:  # 500公尺內
            return similarityDict['Distance'][1][1]
        elif Distance <= similarityDict['Distance'][2][0]:  # 1000公尺內
            return similarityDict['Distance'][2][1]
        else:  # 1000公尺外
            return 0

    elif CollateralInfo['HouseType'] != 'R1':
        if Distance_R2 <= similarityDict['Distance_R2'][0][0]:  # 100公尺內
            return similarityDict['Distance_R2'][0][1]
        elif Distance_R2 <= similarityDict['Distance_R2'][1][0]:  # 500公尺內
            return similarityDict['Distance_R2'][1][1]
        elif Distance_R2 <= similarityDict['Distance_R2'][2][0]:  # 1000公尺內
            return similarityDict['Distance_R2'][2][1]
        else:  # 1000公尺外
            return 0
    else :
        return 0


# 3 社區、巷弄比較
'''
1. 同社區 4
2. 同路段與巷弄 3
3. 同路段、同巷弄屬性、不同巷弄 2
4. 同巷弄屬性 1
5. 不同
'''
def score3_community_or_alley(self, CollateralInfo, NearCase, similarityDict):

    CollateralIsAlley = CollateralInfo['isAlley']
    CollateralCommunityNbr = CollateralInfo['CommunityNbr']

    CollateralRoad = CollateralInfo['road']
    CollateralSection = CollateralInfo['section']
    CollateralLane = CollateralInfo['lane']
    CollateralAlley = CollateralInfo['alley']
    

    if CollateralInfo['HouseType'] == 'R1':
        if NearCase['addressNearLevel'] == similarityDict['Alley'][0][0][0]:
            return similarityDict['Alley'][0][1]  # 3 同巷弄屬性
        elif NearCase['addressNearLevel'] == similarityDict['Alley'][1][0]:
            return similarityDict['Alley'][1][1]  # 2 同巷弄屬性，同路段
        elif NearCase['addressNearLevel'] == similarityDict['Alley'][2][0]:
            return similarityDict['Alley'][2][1]  # 1 同巷弄屬性
        else:
            return similarityDict['Alley'][3][1]  # 1 不同巷弄屬性
        
    elif CollateralInfo['HouseType'] != 'R1':
        if NearCase['CommunityNbr'] == CollateralCommunityNbr and NearCase['CommunityNbr'] != '':
            return similarityDict['Community'][0][1]
        else :
            return 0
    else:
        # print('not R1')
        return 0


# 4 樓層位置比較
def score4_floor(self, CollateralInfo, NearCase, similarityDict):

    CollateralFloorCode = int(CollateralInfo['FloorCode'])
    CollateralTotalFloor = int(CollateralInfo['TotalFloor'])
    CollateralFloorOtherCnt = int(CollateralInfo['FloorOtherCnt'])
    
    floorDiff = abs(int(NearCase['FloorCode']) - CollateralFloorCode)
    
    if CollateralInfo['HouseType'] != 'R1'  and CollateralFloorCode not in  (998, 999) and int(NearCase['FloorCode']) not in  (998, 999):         
        if floorDiff <= similarityDict['Floor_R2'][0][0]:  # 差3樓內
            return similarityDict['Floor_R2'][0][1]
        elif floorDiff <= similarityDict['Floor_R2'][1][0]: # 差8樓內
            return similarityDict['Floor_R2'][1][1]
        else:
            return 0
        
    elif CollateralInfo['HouseType'] == 'R1':         
        if int(NearCase['FloorCode']) == CollateralFloorCode and CollateralFloorCode != 999 and int(NearCase['FloorCode']) != 999:  # 同樓層
            return similarityDict['Floor'][0][1]
        elif CollateralFloorCode not in  (1, 999, 998) and CollateralTotalFloor != CollateralFloorCode  and int(NearCase['TotalFloorCode']) != int(NearCase['FloorCode']) and  int(NearCase['FloorCode']) not in  (1, 999, 998) and int(NearCase['FloorCode']) > 0: # 同屬其他樓     
            return similarityDict['Floor'][1][1]
        else:
            return 0
        
    else:
        return 0


# 5 坪數差異比較
def score5_area(self, CollateralInfo, NearCase, similarityDict):

    CollateralReCalFloorage = CollateralInfo['ReCalFloorage']
    areaDiffPercent = abs((NearCase['BuildingArea'] - CollateralReCalFloorage) / CollateralReCalFloorage)  # 坪數差異比例
    
    if areaDiffPercent <= similarityDict['Ping'][0][0]:  # 差異30%內
        return similarityDict['Ping'][0][1]
    elif areaDiffPercent <= similarityDict['Ping'][1][0]:  # 差異50%內
        return similarityDict['Ping'][1][1]
    else:  # 差異50%以上
        return 0


# 6 屋齡比較
def score6_age(self, CollateralInfo, NearCase, similarityDict):

    CollateralAge = CollateralInfo['Age']
    ageDiff = abs(NearCase['Age'] - CollateralAge)  # 屋齡差異值
    
    if CollateralInfo['HouseType'] == 'R1':
        if ageDiff <= similarityDict['Age'][0][0]:  # 3年內
            return similarityDict['Age'][0][1]
        elif ageDiff <= similarityDict['Age'][1][0]:  # 5年內
            return similarityDict['Age'][1][1]
        elif ageDiff <= similarityDict['Age'][2][0]:  # 5年內
            return similarityDict['Age'][2][1]
        else:  # 10年以上
            return 0
    
    elif CollateralInfo['HouseType'] != 'R1':
        if ageDiff <= similarityDict['Age_R2'][0][0]:  # 3年內
            return similarityDict['Age_R2'][0][1]
        elif ageDiff <= similarityDict['Age_R2'][1][0]:  # 5年內
            return similarityDict['Age_R2'][1][1]
        elif ageDiff <= similarityDict['Age_R2'][2][0]:  # 5年內
            return similarityDict['Age_R2'][2][1]
        else:  # 10年以上
            return 0

    else:
        return 0
        
    


# 7 巷弄屬性
def score7_alley(self, CollateralInfo, NearCase, similarityDict):
    CollateralAlley = CollateralInfo['alley']
    if NearCase['addressNearLevel'] == similarityDict['Alley'][0][0][0] and NearCase['Distance'] <= similarityDict['Alley'][0][0][1]:
        return similarityDict['Alley'][0][1]  # 3 同巷弄屬性，同路段巷巷弄且距離<=200
    elif NearCase['addressNearLevel'] == similarityDict['Alley'][1][0]:
        return similarityDict['Alley'][1][1]  # 2 同巷弄屬性，同路段
    elif NearCase['addressNearLevel'] == similarityDict['Alley'][1][0]:
        return similarityDict['Alley'][2][1]  # 1 同巷弄屬性
    else:
        return similarityDict['Alley'][3][1]  # 1 不同巷弄屬性

# score algo
def similarity_caculate(self, NearCase, similarityDict):
    # 查詢擔保品資訊
    CollateralInfo = self.dfCollateral[self.dfCollateral['ApplNo'] == NearCase['ApplNo']].iloc[0]

    is_ingore = self.case_ingore(CollateralInfo, NearCase)  # 判斷列入計算的案件

    s1_transaction_datediff = self.score1_transaction_datediff(CollateralInfo,NearCase, similarityDict)  # 交易時間差
    s2_distance = self.score2_distance(CollateralInfo,NearCase, similarityDict)  # 距離
    s3_community_or_alley = self.score3_community_or_alley(CollateralInfo, NearCase, similarityDict)  # 同社區或同巷弄屬性
    s4_floor = self.score4_floor(CollateralInfo, NearCase, similarityDict)  # 樓層
    s5_area = self.score5_area(CollateralInfo, NearCase, similarityDict)  # 坪數
    s6_age = self.score6_age(CollateralInfo, NearCase, similarityDict)  # 屋齡

    result = [is_ingore, s1_transaction_datediff, s2_distance, s3_community_or_alley, s4_floor, s5_area, s6_age]  # 結果

    return result


def floorMappingAndCheckDigit(self, x):
    res = self.TotalFloorMapping[x] if x in self.TotalFloorMapping.keys() else x
    res = int(res) if str(res).isdigit() else 9999
    return res

scoreParameter_v2 = {
    'DealMonthDiff': [[6, 62], [12, 60], [24, 55]],
    'Distance': [[200, 7], [500, 4], [1000, 1]],
    'Alley': [[[3, 5000], 12], [2, 9], [1, 8], [0, 0]],
    'Floor': [['same', 3], ['other', 1]],
    'Ping': [[0.3, 2], [0.5, 1]],
    'Age': [[3, 10], [5, 5], [10, 1]],
    'Distance_R2': [[100, 15], [500, 10], [1000, 5]],
    'Community': [['same', 4], ['similar', 3]],
    'Alley_R2': [[[3, 5000], 11], [2, 9], [1, 8], [0, 0]],
    'Floor_R2': [[3, 3], [8, 1]],
    'Age_R2': [[3, 10], [5, 5], [10, 2]],
}

version_int = '2'
use_score_parameter = scoreParameter_v2

dfCompareCases_caculate = dfCompareCases.copy()

print('computing...')
dfCompareCases_caculate[f'v{version_int}_result'] = dfCompareCases_caculate.apply(lambda x: dgis.similarity_caculate(x, use_score_parameter), axis=1)

print('summarizing...')
dfCompareCases_caculate[f'v{version_int}_ignore'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: x[0])

dfCompareCases_caculate[f'v{version_int}_s1_deal_datediff'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: x[1])
dfCompareCases_caculate[f'v{version_int}_s2_distance'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: x[2])
dfCompareCases_caculate[f'v{version_int}_s3_community_or_alley'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: x[3])
dfCompareCases_caculate[f'v{version_int}_s4_floor'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: x[4])
dfCompareCases_caculate[f'v{version_int}_s5_area'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: x[5])
dfCompareCases_caculate[f'v{version_int}_s6_age'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: x[6])

dfCompareCases_caculate[f'v{version_int}_similarity'] = dfCompareCases_caculate[f'v{version_int}_result'].apply(lambda x: sum(x[1:]))

print('sorting...')
dfCompareCases_caculate = dfCompareCases_caculate.sort_values(['ApplNo', f'v{version_int}_similarity'], ascending=False)
dfCompareCases_caculate = dfCompareCases_caculate.reset_index(drop=1)
dfCompareCases_caculate.head()
datetime.now()