# ToDO: clean the column names to avoid error in spark sql 
from fastapi import FastAPI,HTTPException,Cookie,Depends
from fastapi.responses import JSONResponse
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pyspark.sql import SparkSession
from pydantic import BaseModel
from typing import Union
import shutil
import os
import re
import io
import json
from huggingface_hub import InferenceClient
from transformers import pipeline
import matplotlib.pyplot as plt
import seaborn as sns
from utils.prompts import *
import base64
from dotenv import load_dotenv
from decimal import Decimal
import sqlite3
import hashlib
import jwt
from datetime import datetime, timedelta
load_dotenv()
client = InferenceClient(
    provider="cerebras",
    api_key=os.environ.get("HF_TOKEN"),
)

# pipe = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct",use_auth_token=os.environ.get("HF_TOKEN"))

os.makedirs("/app/data",exist_ok=True)
os.makedirs("/app/userData",exist_ok=True)


# Function to clean column names
def clean_column_name(col_name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', col_name)
class request(BaseModel):
    dbName: str

class query(BaseModel):
    dbName: str
    userQuery: str
    chatName: str

class SingleMessage(BaseModel):
    type: str
    sender: str
    content: Union[str, List[dict]]
    code: str

class Messages(BaseModel):
    chatName: str
    messages: List[SingleMessage]

class chat(BaseModel):
    chatName: str

class User(BaseModel):
    username: str
    password: str

app= FastAPI()
spark = SparkSession.builder \
    .appName("DeltaSession") \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Initialize DB once
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

ACCESS_TOKEN_EXPIRE_DAYS = 1
SECRET_KEY = "your-secret"
ALGORITHM = "HS256"

def create_access_token(data):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # PyJWT: jwt.encode(payload, key, algorithm) :contentReference[oaicite:1]{index=1}



# Allow all origins (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_decimals(obj):
    if isinstance(obj, list):
        return [normalize_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: normalize_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)  # or str(obj) if you want to preserve formatting
    else:
        return obj


def model_response(prompt,model="local"):
    message=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
    
    if model=="local":
        return pipe(message)
    else:
        completion = client.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct",
                messages=message,
                # tools=[model_tool],
                tool_choice="auto",
                max_tokens=1500,
            )
        response=completion.choices[0].message.content
        return response

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


        
def sqlQuery(metadata,message):
    prompt=make_sql_prompt(metadata,message)
    response=model_response(prompt=prompt,model="hosted")
    print(response)
    error_resolved=False
    count=0
    while not error_resolved and count<5:
        try:
            result=spark.sql(response)
            error_resolved=True
        except Exception as error:
            print(error)
            refined_prompt=make_sql_refinement_prompt(metadata,message,response,error)
            response=model_response(prompt=refined_prompt,model="hosted")
            count+=1
    
    result=result.collect()
    finalResult=normalize_decimals([row.asDict() for row in result])
    finalResult={"queryResp":finalResult,"sqlQuery":response}
    return finalResult

def plotQuery(metadata,message):
    prompt=get_plot_code_prompt(metadata,message)
    response=model_response(prompt=prompt,model="hosted")
    error_resolved=False
    count=0
    while not error_resolved and count<5:
        try:
            exec(response)
            
            error_resolved=True
        except Exception as error:
            # print(error)
            plt.close()
            refined_prompt=get_plot_code_refinement_prompt(message,metadata,response,error)
            response=model_response(prompt=refined_prompt,model="hosted")
            count+=1
    
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches=None, pad_inches=0.1)
    buf.seek(0)
    img_bytes = buf.read()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    buf.close()
    plt.close()
    finalResult = f"data:image/png;base64,{img_base64}"
    finalResult={"queryResp":finalResult,"plotQuery":response}
    return finalResult


def extendMessage(req:Messages):
    chatName=req.chatName
    messages=req.messages
    with open("/app/userData/"+chatName+".ndjson","a") as file:
        for i in messages:
            print(i)
            # file.write(json.dumps(i.dict())+ "\n")
            file.write(i.json() + "\n")
    
    return {"status": "success", "message": "Updated chat messages"}

def getHistory(chatName):
    hist=[]
    if not os.path.exists("/app/userData/"+chatName+".ndjson"):
        return hist

    with open("/app/userData/"+chatName+".ndjson","r") as file:
        for line in file:
            x=json.loads(line)
            dt={}
            if x["type"]!="text":
                dt={k:v for k,v in x.items() if k!="content"}
            else:
                dt={k:v for k,v in x.items() if k!="code"}
                dt["code"]=dt.pop("content")
            hist.append(dt)
    return hist

@app.post("/userQuery")
def UserQuery(query:query):
    dbname=query.dbName
    message=query.userQuery
    chatName=query.chatName
    databasePath=os.path.join("/app","data",dbname)
    metadataPath=os.path.join(databasePath,"metadata.json")
    with open(metadataPath,"r", encoding="utf-8") as file:
        metadata=json.load(file)
    history=getHistory(chatName)

    prompt=get_query_type_prompt(metadata,message,history)
    response=model_response(prompt=prompt,model="hosted")
    response=json.loads(response)
    if response["type"]=="table":
        finalResult=sqlQuery(metadata,response["queryResp"])
        userMessage={"type":"text","sender":"user","content":message,"code":""}
        modelMessage={"type":"table","sender":"model","content":finalResult["queryResp"],"code":finalResult["sqlQuery"]}
        messages={"chatName":chatName,"messages":[userMessage,modelMessage]}
        messages_obj=Messages(**messages)
        extendMessage(messages_obj)
    elif response["type"]=="plot":
        finalResult=plotQuery(metadata,response["queryResp"])
        userMessage={"type":"text","sender":"user","content":message,"code":""}
        modelMessage={"type":"plot","sender":"model","content":finalResult["queryResp"],"code":finalResult["plotQuery"]}
        messages={"chatName":chatName,"messages":[userMessage,modelMessage]}
        messages_obj=Messages(**messages)
        extendMessage(messages_obj)
    else:
        userMessage={"type":"text","sender":"user","content":message,"code":""}
        modelMessage={"type":"text","sender":"model","content":response["queryResp"],"code":""}
        messages={"chatName":chatName,"messages":[userMessage,modelMessage]}
        messages_obj=Messages(**messages)
        extendMessage(messages_obj)
        return JSONResponse(content=response)

    return JSONResponse(content={"type":response["type"],"queryResp":finalResult["queryResp"]})

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

@app.get("/allChats")
def getChatNames():
    directory = "/app/userData"

    # List only files (excluding directories)
    files = [f.split(".")[0] for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    return JSONResponse(content={"chatNames":files})


@app.post("/getMessages")
def getMessages(req:chat):
    chatName=req.chatName
    messages=[]
    with open("/app/userData/"+chatName+".ndjson","r") as file:
        for line in file:
            x=json.loads(line)
            dt={k:v for k,v in x.items() if k!="code"}
            messages.append(dt)
    
    return JSONResponse(content={"messages":messages})

@app.post("/deleteChat")
def delChat(req:chat):
    chatName=req.chatName
    os.remove("/app/userData/"+chatName+".ndjson")
    return {"status": "success", "message": "Chat Removed"}


def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Missing access token")
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token")

@app.post("/signup")
def signup(user:User):
    username=user.username
    password=user.password
    hashed_pass=hash_password(password)
    try:
     with sqlite3.connect("users.db") as conn:
        conn.execute("insert into users (username,password) values (?,?)",(username,hashed_pass))
        return {"status": "ok","message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    
@app.post("/login")
def login(user:User):
    username=user.username
    password=user.password
    hashed_pass=hash_password(password)
    with sqlite3.connect("users.db") as conn:
        res=conn.execute("select * from users where username=? and password=?",(username,hashed_pass))
        res=res.fetchone()
        if not res:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": username})

    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie("access_token", access_token, httponly=True, max_age=900, path="/", samesite="Lax",secure=False)
    return response

@app.post("/logout")
def logout():
    resp = JSONResponse({"message": "Logged out"})
    resp.delete_cookie("access_token",  path="/")
    return resp

@app.post("/refresh")
def refresh_token(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token")

    new_access = create_access_token({"sub": username})

    response = JSONResponse({"message": "Token refreshed"})
    response.set_cookie("access_token", new_access, httponly=True, max_age=900, path="/", samesite="None")
    return response

@app.post("/auth-status")
def auth_status(username: str = Depends(get_current_user)):
    return {"status": "ok", "user": username}