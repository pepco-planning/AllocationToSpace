def hierarchyMap():
    return """
        select Department,
            VMDepartment
        from ats.HierarchyMap;
    """


def mods_Furniture():
    return """
        select FurnitureType, 
            DisplayMods
        from ats.Mods_Furniture;
    """


def mods_ExtraSpace():
    return """
        select Week,
            Department,
            DisplayMods as DisplayModsES
        from ats.Mods_ExtraSpace;
    """


def mods_HotSpot():
    return """
        select Week,
            Department,
            DisplayMods as DisplayModsHS
        from ats.Mods_HotSpot;
    """


def mods_Tops():
    return """
        select Week,
            Department,
            DisplayMods as DisplayModsT
        from ats.Mods_Tops;
    """


def retailPerMod():
    return """
        select Department,
            RetailPerDisplayMod
        from ats.RetailPerMod;
    """


def result_bulkInsert(tableName, filePath):
    return """
        bulk insert """ + tableName + """ 
        from '""" + filePath + r"""'
        with (
            rows_per_batch = 10000,
            firstrow = 2,
            fieldterminator = ',',
            rowterminator = '\n',
            tablock);
    """
