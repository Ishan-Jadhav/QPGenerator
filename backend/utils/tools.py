def sqlQuery(spark,query):
    res=spark.sql(query)
    return res

def plotQuery():
    pass