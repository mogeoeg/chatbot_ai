from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import psycopg2
import json
import re

app = FastAPI()

api_key = "AIzaSyA7qBvXge6Ss6_D8SMAK982C1cT3ZfZgjM"
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

generation_config = {
    "temperature": 0.1
}

safety_settings = [
    {"category": "HARM_CATEGORY_DANGEROUS", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

class ChatMessage(BaseModel):
    message: str

def get_schema_details():
    connection = psycopg2.connect(
        dbname="postgres",
        user="postgres.edqjhuymghuhvtdonxup",
        password="FH5ipTRakSkH9u79",
        host="aws-0-ap-south-1.pooler.supabase.com",
        port=6543
    )
    cursor = connection.cursor()
    schema_info = {}

    try:
        # Get tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()
        for (table_name,) in tables:
            # Get columns for each table
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}';")
            columns = [row[0] for row in cursor.fetchall()]
            schema_info[table_name] = columns

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

    return schema_info

def execute_query(clean_query):
    connection = psycopg2.connect(
        dbname="postgres",
        user="postgres.edqjhuymghuhvtdonxup",
        password="FH5ipTRakSkH9u79",
        host="aws-0-ap-south-1.pooler.supabase.com",
        port=6543
    )
    cursor = connection.cursor()
    try:
        print("Executing Query:", clean_query)  # Debugging line
        cursor.execute(clean_query)
        
        columns = [desc[0] for desc in cursor.description]
        print("Cursor Description:", cursor.description)  # Debugging line
        result = cursor.fetchall()
        print("Raw Query Result:", result)  # Debugging line
        data = [dict(zip(columns, row)) for row in result]
        print("Processed Query Result:", data)

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()
    return data

@app.post("/chat/")
async def chat(message: ChatMessage):
    schema_details = get_schema_details()
    schema_info_str = json.dumps(schema_details, indent=2)

    response = model.generate_content([
        f"""
        You are a helpful assistant. The user has asked:
        '{message.message}'
        Generate a SQL query to fetch the required data from the database.
        The database schema is as follows:
        {schema_info_str}
        Return only the SQL query without any markdown or code block formatting.
        example:
        give me details about username or give me details for username
        Dont forget to add this ; end of query
        Apply the query as by getting from user dont change to casesensitive
        get the key work from user queries and analyze db where it matched then make sql queries
        Example:
        ask :give me details karthik
        you should generate like this
        SELECT * FROM users WHERE name = 'karthik';
        Dont like this
        SELECT * FROM users WHERE name = 'Karthik';
        """,
    ], safety_settings=safety_settings, generation_config=generation_config)
    
    response_text = response.text.strip()
    clean_query = re.sub(r'```[\s\S]*?```', '', response_text).strip()
    
    # if not clean_query.lower().startswith("select"):
    #     raise HTTPException(status_code=400, detail="Invalid SQL query generated")
    # print(clean_query)

    try:
        results = execute_query(clean_query)
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Chatbot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
