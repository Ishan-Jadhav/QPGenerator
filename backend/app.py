# ToDO: clean the column names to avoid error in spark sql 
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pyspark.sql import SparkSession
from pydantic import BaseModel
import shutil
import os
import re
import json
from huggingface_hub import InferenceClient
from utils.prompts import make_sql_prompt,make_sql_refinement_prompt
client = InferenceClient(
    provider="cerebras",
    api_key="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",
)


# Function to clean column names
def clean_column_name(col_name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', col_name)
class request(BaseModel):
    dbName: str

class query(BaseModel):
    dbName: str
    userQuery: str


app= FastAPI()
spark = SparkSession.builder \
    .appName("DeltaSession") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Allow all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/registerDB")
def register(dbName:request):
    name=dbName.dbName
    databasePath=os.path.join("/app","data",name)
    files=os.walk(databasePath)
    spark.sql(f"create database if not exists {name}")
    for file in files:
        for i in file[2]:
            fileName=i
            if len(fileName.split("."))==2 and fileName.split(".")[1]=="csv":
                fn=clean_column_name(fileName.split(".")[0])
                deltaPath=os.path.join(databasePath,fn)
                spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS {name}.{fn}
                    USING DELTA
                    LOCATION '{deltaPath}'
                """)
    return {"status": "success", "message": "Registered"}


        


    
@app.post("/userQuery")
def UserQuery(query:query):
    dbname=query.dbName
    message=query.userQuery
    databasePath=os.path.join("/app","data",dbname)
    metadataPath=os.path.join(databasePath,"metadata.json")
    with open(metadataPath,"r", encoding="utf-8") as file:
        metadata=json.load(file)
    prompt=make_sql_prompt(metadata,message)
    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        # tools=[model_tool],
        tool_choice="auto",
        max_tokens=500,
    )
    response=completion.choices[0].message.content
    error_resolved=False
    count=0
    while not error_resolved and count<5:
        try:
            result=spark.sql(response)
            error_resolved=True
        except Exception as error:
            print(error)
            refined_prompt=make_sql_refinement_prompt(metadata,message,response,error)
            completion = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct",
                messages=[
                    {
                        "role": "user",
                        "content": refined_prompt
                    }
                ],
                # tools=[model_tool],
                tool_choice="auto",
                max_tokens=500,
            )
            response=completion.choices[0].message.content
            count+=1
    
    result=result.collect()
    finalResult=[row.asDict() for row in result]
    return JSONResponse(content={"queryResp":finalResult})

@app.get("/database-names")
def get_dbs():
    directoryPath=os.path.join("/app","data")
    names=os.listdir(directoryPath)
    names=[name for name in names if os.path.isdir(os.path.join(directoryPath, name))]
    return JSONResponse(content={"folders":names})


def NewDB(dbName):
    name=dbName
    databasePath=os.path.join("/app","data",name)
    files=os.walk(databasePath)
    spark.sql(f"create database if not exists {name}")
    for file in files:
        for i in file[2]:
            fileName=i
            if len(fileName.split("."))==2 and fileName.split(".")[1]=="csv":
                fn=clean_column_name(fileName.split(".")[0])
                csvPath=os.path.join(databasePath,fileName)
                deltaPath=os.path.join(databasePath,fn)
                print(deltaPath)
                df=spark.read.option("header","true").option("inferSchema","true").csv(csvPath)
                df = df.toDF(*[clean_column_name(col) for col in df.columns])
                if not os.path.exists(deltaPath):
                    df.write.format("delta").mode("overwrite").save(deltaPath)
                spark.sql(f"""
                    CREATE TABLE IF NOT EXISTS {name}.{fn}
                    USING DELTA
                    LOCATION '{deltaPath}'
                """)
    
    return {"status": "success", "message": "Created New DB"}


@app.post("/upload-database")
async def upload_data(
    db_name: str = Form(...),
    metadata_file: UploadFile = File(...),
    table_files: List[UploadFile] = File(...)
    ):
    os.makedirs(f"/app/data/{db_name}", exist_ok=True)
    meta_path = f"/app/data/{db_name}/metadata.json"
    with open(meta_path, "wb") as f:
        shutil.copyfileobj(metadata_file.file, f)
    for file in table_files:
        file_path = f"/app/data/{db_name}/{file.filename}"
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

    NewDB(db_name)

    return {"status": "success", "message": "Files uploaded"}
    

