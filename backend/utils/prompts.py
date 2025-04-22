
def get_query_type_prompt(metadata, user_query):
    # prompt=f"""
    # You are a query classification model. Given the database schema and a user query, classify the type of response the query is asking for.

    # There are only three possible types of query responses:
    # 1. "text" - A descriptive or explanatory response in natural language.
    # 2. "table" - A request that should be answered with an SQL query (for tabular data).
    # 3. "plot" - A request that should be answered with a visualization (using seaborn).

    # Your task is to ONLY respond with one of: "text", "table", or "plot".

    # ### Database Metadata:
    # {metadata}

    # ### User Query:
    # {user_query}

    # ### Response Type:
    # """
    prompt = f"""
    You are a query classification model. Given the database schema and a user query, classify the type of response the query is asking for.

    There are only three possible types of query responses:
    1. "text" - A descriptive or explanatory response in natural language.
    2. "table" - A request that should be answered with an SQL query (for tabular data).
    3. "plot" - A request that should be answered with a visualization (using seaborn).

    Your task is to respond in one of the following **pure dictionary formats** ONLY:
    - If the query is best answered with a natural language explanation or clarification, respond with:
    {{
        "type": "text",
        "queryResp": "Your explanation here."
    }}
    - If the query is asking for a table or plot, first validate whether the column names or table references mentioned in the user query actually exist in the provided metadata.
        - If any column names or tables mentioned are missing or do not match the metadata, respond with:
        {{
            "type": "text",
            "queryResp": "Your explanation here."
        }}
        - Otherwise, respond with:
        {{ "type": "table" }} or {{ "type": "plot" }} depending on what the query asks for.

    **IMPORTANT: Respond ONLY with a valid Python dictionary. DO NOT include any explanations, headings, markdown formatting, or additional text.**

    ### Database Metadata:
    {metadata}

    ### User Query:
    {user_query}

    ### Response:
    """


    return prompt.strip()

def make_sql_prompt(metadata,user_question):
    prompt = f"""
    You are a SQL-generation assistant.

    Database metadata (databases → tables):
    {metadata}

    User question:
    {user_question}

    Generate the corresponding SQL query using fully qualified table names
    (in the form database_name.table_name) and return *only* the SQL string.
    """
    return prompt.strip()

def make_sql_refinement_prompt(metadata, user_question, initial_sql_query, error_message):

    prompt = f"""
    You are an SQL assistant.

    Database Metadata:
    {metadata}

    User Question:
    {user_question}

    Initial SQL Query:
    {initial_sql_query}

    Error Message:
    {error_message}

    Please refine the SQL query using the provided database metadata, user question, initial SQL query, and error message. Return only the corrected SQL query without any explanations or comments.
    """
    return prompt.strip()

def get_plot_code_prompt(metadata, user_query):
    prompt = f"""
    You are a code generation model. Your task is to generate Python code that produces a plot based on the given user query and database schema.

    ### Output Rules:
    - Output must be raw Python code only.
    - Do NOT add the word "python" or any language identifier at the top.
    - Do NOT include triple backticks or markdown formatting.
    - Do NOT include any explanation or comments.
    - Do NOT include any import statements. All required libraries are already imported.

    ### Requirements:
    - Assume an active Spark session is already created and available as `spark`.
    - Use only `SELECT` queries in `spark.sql("...")` to retrieve data.
    - SQL queries must use fully qualified table names in the form: `SELECT ... FROM database_name.table_name`.
    - **Do NOT modify the database in any way.** Absolutely no `INSERT`, `UPDATE`, `DELETE`, `DROP`, or other write operations.
    - Convert the result to a pandas DataFrame using `.toPandas()`.
    - Use only the following libraries for data processing and visualization (already imported):
        - seaborn as sns
        - matplotlib.pyplot as plt
        - pandas as pd
        - numpy

    ### Database Metadata:
    {metadata}

    ### User Query:
    {user_query}

    ### Python Code:
    """
    return prompt.strip()

def get_plot_code_refinement_prompt(user_query, metadata, previous_code, error_message):
    prompt = f"""
    You are a code refinement model. The user wants to generate a plot using Spark SQL and seaborn. The previous code failed with an error. Your task is to generate a corrected version of the code based on the original intent and the error message.

    ### Output Rules:
    - Output must be raw Python code only.
    - Do NOT add the word "python" or any language identifier at the top.
    - Do NOT include triple backticks or markdown formatting.
    - Do NOT include any explanation or comments.
    - Do NOT include any import statements. All required libraries are already imported.

    ### Requirements:
    - Assume an active Spark session is already created and available as `spark`.
    - Use only `SELECT` queries in `spark.sql("...")` to retrieve data.
    - SQL queries must use fully qualified table names in the form: `SELECT ... FROM database_name.table_name`.
    - **Do NOT modify the database in any way.** Absolutely no `INSERT`, `UPDATE`, `DELETE`, `DROP`, or other write operations.
    - Use `.toPandas()` to convert Spark DataFrame to pandas.
    - Only use the following libraries for data processing and visualization (already imported):
        - seaborn as sns
        - matplotlib.pyplot as plt
        - pandas as pd
        - numpy
    - Do NOT import any other libraries.
    - Do NOT create or configure a Spark session.

    ### User Query:
    {user_query}

    ### Database Metadata:
    {metadata}

    ### Previous Code:
    {previous_code}

    ### Error Message:
    {error_message}

    ### Corrected Python Code:
    """
    return prompt.strip()
