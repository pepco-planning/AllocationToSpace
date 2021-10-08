# all not closed stores
def storeList():
    return """
        EVALUATE
        SUMMARIZECOLUMNS (
        
            'Stores STR'[STR Number],
           
            FILTER (
                VALUES ( 'Stores STR'[STR Opened] ),
                NOT ( 'Stores STR'[STR Opened] IN { "Closed" } )
            ),
           
            FILTER (
                VALUES ( 'Stores STR'[STR Warehouse Type] ),
                'Stores STR'[STR Warehouse Type] IN { "Store" }
            )
        );   
    """


def hierarchyTable():
    return """
        EVALUATE
        SUMMARIZECOLUMNS (
        
            'Product Hierarchy PRH'[PRH Department],
            'Product Hierarchy PRH'[PRH Category],
            'Product Hierarchy PRH'[PRH Category ID],
                         
            FILTER (
                VALUES ( 'Product Hierarchy PRH'[PRH Division] ),
                ( 'Product Hierarchy PRH'[PRH Division] IN { "a Clothing", "b Nonclothing" } )
            ),
           
            FILTER (
                VALUES ( 'Product Hierarchy PRH'[PRH Category] ),
                NOT ( ISBLANK('Product Hierarchy PRH'[PRH Category]) )
            )
           
        );
    """


# YearWeek with start dates table of current and one next seasons
def weekTable():
    return """
        DEFINE
        var Sn = CALCULATE(MAX('Planning Calendar PCAL'[Pl Season]),'Planning Calendar PCAL'[Pl Day]=(TODAY() - 1))
        var Yr = CALCULATE(MAX('Planning Calendar PCAL'[Pl Year]),'Planning Calendar PCAL'[Pl Day]=(TODAY() - 1))
        
        var StartWk = CALCULATE(MIN('Planning Calendar PCAL'[PCAL_WEEK_KEY]),'Planning Calendar PCAL'[Pl Year]=Yr,'Planning Calendar PCAL'[Pl Season]=Sn)
        var EndWk =
        SWITCH(
            TRUE(),
            Sn = "S1 Winter", CALCULATE(MAX('Planning Calendar PCAL'[PCAL_WEEK_KEY]),'Planning Calendar PCAL'[Pl Season] = "S2 Summer", 'Planning Calendar PCAL'[Pl Year] = Yr),
            Sn = "S2 Summer", CALCULATE(MAX('Planning Calendar PCAL'[PCAL_WEEK_KEY]),'Planning Calendar PCAL'[Pl Season] = "S1 Winter", VALUE('Planning Calendar PCAL'[Pl Year]) = Yr+1)
        )
        
        EVALUATE
        SUMMARIZECOLUMNS (
        
            'Planning Calendar PCAL'[PCAL_WEEK_KEY],
             
            FILTER (
                VALUES ( 'Planning Calendar PCAL'[PCAL_WEEK_KEY] ),
                'Planning Calendar PCAL'[PCAL_WEEK_KEY] >= StartWk
                    && 'Planning Calendar PCAL'[PCAL_WEEK_KEY] <= EndWk
            ),
           
            "StartDate",
            FORMAT(FIRSTDATE('Planning Calendar PCAL'[Issue Date]), "yyyy-MM-dd")
         
         )
    """


# SalesMix counted per week:
# SalesMix[X] = (Cat[X] + Cat[X+1] + Cat[X + 2]) / (Dep[X] + Dep[X+1] + Dep[X+2])
# where Cat[a] is a sales value in a-week, etc...
# the endWeek doesn't have to be increase by 2 weeks
# it's implemented in the dax code
# an example of startWeek(endWeek): 202105
def salesMixTable(startWeek, endWeek):
    return """
    EVALUATE
    SUMMARIZECOLUMNS (
        'Product Hierarchy PRH'[PRH Department],
        'Product Hierarchy PRH'[PRH Category],
        'Planning Calendar PCAL'[PCAL_WEEK_KEY],
          
        FILTER (
            VALUES ( 'Product Hierarchy PRH'[PRH Group] ),
            NOT ( 'Product Hierarchy PRH'[PRH Group] IN { "c Seasonal" } )
        ),
      
        FILTER (
            VALUES ( 'Planning Calendar PCAL'[PCAL_WEEK_KEY] ),
            'Planning Calendar PCAL'[PCAL_WEEK_KEY] >= """ + str(startWeek) + """ 
                && 'Planning Calendar PCAL'[PCAL_WEEK_KEY] <= """ + str(endWeek) + """ 
        ),
       
      
        "SalesValue",
            IF ( [Sales Retail Report dsale] < 0, 0, [Sales Retail Report dsale] ),
       
        "CategoryMix",
            VAR OpeningWeek = MAX('Planning Calendar PCAL'[PCAL_WEEK_KEY])
            VAR ClosingDate = DATEADD ( FIRSTDATE ( 'Planning Calendar PCAL'[Issue Date] ), 14, DAY )
            VAR ClosingWeek = CALCULATE(MAX('Planning Calendar PCAL'[PCAL_WEEK_KEY]),'Planning Calendar PCAL'[Issue Date]=ClosingDate)
               
            RETURN
            DIVIDE(
                CALCULATE(
                    IF ( [Sales Retail Report dsale] < 0, 0, [Sales Retail Report dsale] ),
                    FILTER(
                        ALL('Planning Calendar PCAL'),
                        'Planning Calendar PCAL'[PCAL_WEEK_KEY] >= OpeningWeek &&
                        'Planning Calendar PCAL'[PCAL_WEEK_KEY] <= ClosingWeek
                        )
                    ),
                CALCULATE(
                    IF ( [Sales Retail Report dsale] < 0, 0, [Sales Retail Report dsale] ),
                        FILTER(
                            ALL('Planning Calendar PCAL'),
                            'Planning Calendar PCAL'[PCAL_WEEK_KEY] >= OpeningWeek &&
                            'Planning Calendar PCAL'[PCAL_WEEK_KEY] <= ClosingWeek
                            ),
                    REMOVEFILTERS ( 'Product Hierarchy PRH'[PRH Category] ))
                )
    )
    """