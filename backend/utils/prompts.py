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

