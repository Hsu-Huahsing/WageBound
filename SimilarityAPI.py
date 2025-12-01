# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 14:31:17 2024

@author: Z00051711
"""

import requests as re

url = r"http://dgisapiuat.ctbcbank.com/dgis/dgisapi/AccurateEstimation"

payload = {"SysType":"DGIS",
           "SubSysType":"01",
           "Account":"Z00002809",
           "Location":{
               "City":"006",
               "Town":"302",
               "Address":"",
               "OAddr":"",
               "CompareLV":"2",
               "X":252814.544299987,
               "Y":2745217.89140835,
               "FishID":829466
               },
           "RequestOption":{
               "IsFishIDUpdate":"Y",
               "IsHighRiskUpdate":"Y",
               "IsNegativeUpdate":"Y",
               "IsSectorCodeUpdate":"N",
               "IsAreaGradeFinalUpdate":"N"
               },
           "CollateralData":{
               "CollateralNo":"30201",
               "CaseNo":"20230802EI00023_0",
               "LoanPurpose":"01",
               "ProjectName":"昌益-音樂廳",
               "Builder":"",
               "Age":21.0,
               "HouseType":"R2",
               "TotalFloor":"10",
               "FloorCode":"5",
               "FloorPublic":"0",
               "UseType":"01",
               "BuildingMaterial":"01",
               "BuildingReg":"01",
               "RoadWidth":8.0,
               "UseArea":"00",
               "UseAreaTYPE":"F",
               "SurRoundings":"",
               "AnnouncementPrice":33.06,
               "TotalFloorage":50.27,
               "IndoorFloorage":29.57,
               "ReCalFloorage":42.27,
               "PublicFloorage":12.70,
               "BasementFloorage":0.0,
               "TerraceFloorage":0.0,
               "LandArea":9.88,
               "TotalPrice":2100.0000,
               "ParkingSpaceTotalPrice":100.0000,
               "ParkingSpaces":[{
                   "ID":"1",
                   "Type":"04",
                   "Floor":"B2",
                   "Area":8.00}],
               "MainBuilding":1,
               "BuildCommercialCnt":0,
               "BuildHouseCommercialCnt":0,
               "BuildHouseCnt":1,
               "BuildIndustryCnt":0,
               "BuildPublicCnt":0,
               "isBasement":"N",
               "FloorOtherCnt":1,
               "FloorFirstCnt":1,
               "FloorTopCnt":0,
               "FloorOverAllCnt":0,
               "InCaseNo":"",
               "isBulkCase":"N",
               "BulkCaseNo":"",
               "BulkCasePhaseNo":"",
               "BulkCaseSection":"",
               "BulkCaseHousingNo":"",
               "BulkCaseHousingFloor":"5",
               "RefUnitPrice":47.3149,
               "Fireinsurance":380.0,
               "SectorCode":"0435",
               "AreaGradeFinal":"A",
               "CommunityNbr":"",
               "LatestAuditResultGap1year":"",
               "LatestPresumeUnit":-9999.0,
               "LatestLandPrice":-9999.0,
               "LatestStallAppraisePrice":-9999.0,
               "LatestTotalCurrentPrice":-9999.0,
               "AuditResultGapYear":-9999,
               "PolicyHpi":-9999.0
               },
           "LegacyItem":{
               "Hierarchy":[],
               "Negative":[]
               }
           }

res = re.post(url, json=payload)

a = res.json()
