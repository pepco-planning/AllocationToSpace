import pandas as pd
from sys import path
path.append(r"dll")
from pyadomd import Pyadomd

def dataFrameFromMDX(query):
    connStr = "Provider=MSOLAP;Data Source=LB-P-WE-AS;Catalog=PEPCODW"
    conn = Pyadomd(connStr)
    conn.open()
    cursor = conn.cursor()
    cursor.execute(query)

    cursor.arraysize = 5000

    df = pd.DataFrame(cursor.fetchall())

    conn.close()

    return df

