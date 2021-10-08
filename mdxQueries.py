# the number of furnitures per store and VM department
# exclude the season group
def numberOfFurniture():
    return """
        SELECT  
            {
        [Measures].[Sum No Of Furniture dstl]
               } ON 0,  
          NON EMPTY (
        [Stores STR].[STR Number].[STR Number],
        [Products SKU].[VM Department].[VM Department],
        [Store Layouts STL].[STL Furniture Type].[STL Furniture Type]
        )on 1
        
        from (select (
        {
        [Stores STR].[STR Warehouse Type].&[Store]
        },
        {
        [Products SKU].[VM Product Hierarchy].[VM Group].&[a Outerwear],
        [Products SKU].[VM Product Hierarchy].[VM Group].&[b Basic],
        [Products SKU].[VM Product Hierarchy].[VM Group].&[c Accessories],
        [Products SKU].[VM Product Hierarchy].[VM Group].&[d Footwear],
        [Products SKU].[VM Product Hierarchy].[VM Group].&[a Housewares],
        [Products SKU].[VM Product Hierarchy].[VM Group].&[b Toys],
        [Products SKU].[VM Product Hierarchy].[VM Group].&[d FMCG]
        }
        )
        on 0
        
        FROM [Everything])
    """

