import pyodbc


def centralPlanningDB_connect():
    db_conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                             'Server=SharedSQL01-P;'
                             'Database=Central_Planning;'
                             'Trusted_Connection=yes;')
    return db_conn



