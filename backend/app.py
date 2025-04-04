from fastapi import FastAPI
from pyspark.sql import SparkSession
from pydantic import BaseModel
import os
import re




# Function to clean column names
def clean_column_name(col_name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', col_name)
class request(BaseModel):
    dbName: str


app= FastAPI()
spark = SparkSession.builder \
    .appName("DeltaSession") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

spark.sql("show databases").show()

@app.post("/newDB")
def NewDB(dbName:request):
    name=dbName.dbName
    databasePath=os.path.join("/app","data",name)
    files=os.walk(databasePath)
    spark.sql(f"create database if not exists {name}")
    for file in files:
        fileName=file[2][0]
        if len(fileName.split("."))==2 and fileName.split(".")[1]=="csv":
            fn=clean_column_name(fileName.split(".")[0])
            csvPath=os.path.join(databasePath,fileName)
            deltaPath=os.path.join(databasePath,fn)
            print(deltaPath)
            df=spark.read.option("header","true").option("inferSchema","true").csv(csvPath)
            df = df.toDF(*[clean_column_name(col) for col in df.columns])
            df.write.format("delta").mode("overwrite").save(deltaPath)
            spark.sql(f"""
                CREATE TABLE IF NOT EXISTS {name}.{fn}
                USING DELTA
                LOCATION '{deltaPath}'
            """)
            spark.sql(f"select * from {name}.{fn}").show()
        


    
@app.post("/userQuery")
def UserQuery():
    pass
