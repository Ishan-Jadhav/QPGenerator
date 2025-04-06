from pydantic import BaseModel


class sqlParams(BaseModel):
    dbName: str
    query: str

sql_tool={
    "type": "function",
    "function": {
        "name" : "sqlTool",
        "description": "Execute sql query and return result table in json format",
        "parameters": sqlParams.model_json_schema(),
    },
}


def sqlTool(spark,dbName,query):
    pass

