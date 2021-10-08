import daxDownloader as dd
import daxQueries as daxQ
import sqlConnections as sc
import sqlQueries as sqlQ
import mdxDownloader as md
import mdxQueries as mdxQ

import os
import pandas as pd
import datetime
import tqdm
import shutil
from decimal import *


print("### AlloToSpace v 202109 ###")
print("start:", datetime.datetime.now())


targetValue_fileName = "StoreTarget.csv"
# targetValue_filePath_original = r"\\10.2.5.140\zasoby\Planowanie\Space Planning\Allo To Space model"
targetValue_filePath = r"c:\Mariusz"
targetValue_filePathWithName = targetValue_filePath + "\\" + targetValue_fileName
centralPlanning_tableName = "ats.StoreStockTargets"


# raw data downloader
hierarchy = dd.dataFrameFromTabular(daxQ.hierarchyTable())
hierarchy.columns = ["Department", "Category", "CategoryID"]
hierarchy = hierarchy[hierarchy.Department != "a Dump codes"]

departments = hierarchy.Department.unique()


weeks = dd.dataFrameFromTabular(daxQ.weekTable())
weeks.columns = ["Week", "StartDate"]
weeks.Week = weeks.Week.astype("int32")


stores = dd.dataFrameFromTabular(daxQ.storeList())
stores.columns = ["Store"]


hierarchyMap = pd.read_sql(sqlQ.hierarchyMap(), sc.centralPlanningDB_connect())
mods_Furniture = pd.read_sql(sqlQ.mods_Furniture(), sc.centralPlanningDB_connect())
mods_ExtraSpace = pd.read_sql(sqlQ.mods_ExtraSpace(), sc.centralPlanningDB_connect())
mods_HotSpot = pd.read_sql(sqlQ.mods_HotSpot(), sc.centralPlanningDB_connect())
mods_Tops = pd.read_sql(sqlQ.mods_Tops(), sc.centralPlanningDB_connect())
retailPerMod = pd.read_sql(sqlQ.retailPerMod(), sc.centralPlanningDB_connect())


sumNoOfFurniture = md.dataFrameFromMDX(mdxQ.numberOfFurniture())
sumNoOfFurniture.columns = ["Store", "VMDepartment", "FurnitureType", "SumNoOfFurniture"]
sumNoOfFurniture.SumNoOfFurniture = sumNoOfFurniture.SumNoOfFurniture.apply(lambda x: float(str(x).replace(',','.')))


# policz sprzedaz dla zeszłego roku i zamien weeki na obecne, zeby je wykorzystac do policzenia targetu na ten rok
salesMix = dd.dataFrameFromTabular(daxQ.salesMixTable(weeks.Week.min() - 100, weeks.Week.max() - 100))
salesMix.columns = ["Department", "Category", "Week", "SalesValue", "CategoryMix"]
salesMix.Week = salesMix.Week.apply(lambda week: week + 100)
salesMix.Week = salesMix.Week.astype("int32")
# /raw data downloader


# join tables
extraMods = pd.DataFrame(data=departments, columns=["Department"])
extraMods = extraMods.merge(weeks.Week, how="cross")
extraMods = extraMods.merge(mods_ExtraSpace, on=["Department", "Week"], how="left")
extraMods = extraMods.merge(mods_HotSpot, on=["Department", "Week"], how="left")
extraMods = extraMods.merge(mods_Tops, on=["Department", "Week"], how="left")
extraMods.fillna(0, inplace=True)
extraMods["ExtraDisplayMods"] = extraMods.DisplayModsES + extraMods.DisplayModsHS + extraMods.DisplayModsT
extraMods.drop(["DisplayModsES", "DisplayModsHS", "DisplayModsT"], axis=1, inplace=True)
extraMods = extraMods.groupby(["Department", "Week"], as_index=True)["ExtraDisplayMods"].agg("sum")


furnitureMods = sumNoOfFurniture.merge(hierarchyMap, on="VMDepartment", how="left")
furnitureMods.drop("VMDepartment", axis=1, inplace=True)
furnitureMods = furnitureMods.merge(mods_Furniture, on="FurnitureType", how="left")
furnitureMods.drop("FurnitureType", axis=1, inplace=True)
furnitureMods.DisplayMods.fillna(0, inplace=True)
furnitureMods["DisplayModsFM"] = furnitureMods.SumNoOfFurniture.astype('float64') * furnitureMods.DisplayMods
furnitureMods.drop(["SumNoOfFurniture", "DisplayMods"], axis=1, inplace=True)
furnitureMods = furnitureMods.groupby(["Store", "Department"], as_index=True)["DisplayModsFM"].agg("sum")
# /join tables


resultTable = pd.DataFrame(columns=["TargetStartDate",
                                    "SiteCode",
                                    "Group6Code",
                                    "TargetValue",
                                    "MinTargetValue",
                                    "MaxTargetValue",
                                    "ExtraDisplayMods",
                                    "DisplayModsFM",
                                    "PEP_ModifiedDateTime"])
if os.path.isfile(targetValue_fileName):
    os.remove(targetValue_fileName)
resultTable.to_csv(targetValue_fileName, mode="a+", index=False, header=True)


weekHierarchy = hierarchy.merge(weeks, how="cross")

for store in tqdm.tqdm(stores.Store):
    weekHierarchyStore = weekHierarchy
    weekHierarchyStore["Store"] = store
    weekHierarchyStore = weekHierarchyStore.merge(extraMods, on=["Department", "Week"], how="left")
    weekHierarchyStore = weekHierarchyStore.merge(furnitureMods, on=["Store", "Department"], how="left")
    weekHierarchyStore.fillna(0, inplace=True)
    weekHierarchyStore["DisplayMods"] = weekHierarchyStore.ExtraDisplayMods + weekHierarchyStore.DisplayModsFM
    weekHierarchyStore = weekHierarchyStore.merge(retailPerMod, on="Department", how="left")
    weekHierarchyStore.fillna(0, inplace=True)
# ponizszy mnoznik 1.15 jest dodany dla powiekszenia targetu z powodu niewliczanych wczesniej stock roomow
    weekHierarchyStore["DepartmentTarget"] = weekHierarchyStore.DisplayMods * weekHierarchyStore.RetailPerDisplayMod * 1.15
    weekHierarchyStore.drop(["DisplayMods", "RetailPerDisplayMod"], axis=1, inplace=True)
    weekHierarchyStore = weekHierarchyStore.merge(salesMix, on=["Department", "Category", "Week"], how="left")
    weekHierarchyStore.fillna(0, inplace=True)
    weekHierarchyStore["TargetValue"] = weekHierarchyStore.DepartmentTarget * weekHierarchyStore.CategoryMix
    weekHierarchyStore.drop(["DepartmentTarget", "CategoryMix"], axis=1, inplace=True)
    weekHierarchyStore["MinTargetValue"] = 0.9 * weekHierarchyStore.TargetValue
    weekHierarchyStore["MaxTargetValue"] = 1.1 * weekHierarchyStore.TargetValue

    colsToRound = ["TargetValue", "MinTargetValue", "MaxTargetValue"]
    weekHierarchyStore[colsToRound] = weekHierarchyStore[colsToRound].round().astype(int)

    weekHierarchyStore["PEP_ModifiedDateTime"] = datetime.datetime.today().strftime("%Y-%m-%d")

    weekHierarchyStore[["StartDate",
                        "Store",
                        "CategoryID",
                        "TargetValue",
                        "MinTargetValue",
                        "MaxTargetValue",
                        "ExtraDisplayMods",
                        "DisplayModsFM",
                        "PEP_ModifiedDateTime"]].to_csv(targetValue_fileName, mode="a", index=False, header=False)


if os.path.isfile(targetValue_filePathWithName):
    os.remove(targetValue_filePathWithName)
shutil.copy(targetValue_fileName, targetValue_filePathWithName)


# upload data
centralPlanningDB_conn = sc.centralPlanningDB_connect()
centralPlanningDB_cursor = centralPlanningDB_conn.cursor()
centralPlanningDB_cursor.execute("truncate table " + centralPlanning_tableName + ";")
centralPlanningDB_cursor.execute(sqlQ.result_bulkInsert(centralPlanning_tableName,  targetValue_filePathWithName))
centralPlanningDB_cursor.commit()
centralPlanningDB_conn.close()
# /upload data


print("Koniec:", datetime.datetime.now())

