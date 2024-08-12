from fastapi import FastAPI, HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import logging
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

try:
    client = ChatGoogleGenerativeAI(
        api_key='AIzaSyA7qBvXge6Ss6_D8SMAK982C1cT3ZfZgjM',
        model='gemini-1.5-flash' , # Update with the correct model name
        convert_system_message_to_human=True
    )
except KeyError as e:
    logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {str(e)}")
    raise RuntimeError(f"Failed to initialize ChatGoogleGenerativeAI: {str(e)}")

# Database setup (update with your actual database URI)
DATABASE_URI = 'postgresql://postgres.edqjhuymghuhvtdonxup:FH5ipTRakSkH9u79@aws-0-ap-south-1.pooler.supabase.com:6543/postgres'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

class QueryRequest(BaseModel):
    prompt: str

def fetch_data_from_database() -> list:
    """Fetch data from the database."""
    try:
        # Example SQL query; adjust as needed
        sql_query = "SELECT * FROM product"
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            columns = result.keys()  # Get column names
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return rows
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

def process_data_with_ai(data: list, prompt: str) -> Any:
    """Send the fetched data to AI for processing."""
    try:
        data_str = str(data)
        messages = [
            SystemMessage(content="You are a helpful assistant. Process the following data:"),
            HumanMessage(content=f"Process this data: {data_str} and answer the following questions: {prompt}")
        ]
        
        logger.info(f"Sending messages to AI: {messages}")
        response = client.invoke(input=messages)
        logger.info(f"Raw AI response: {response}")
    
        if isinstance(response, dict):
            content = response.get('content')
            print("=============================================")
            if content:
                return {"response": content}
            else:
                raise ValueError("Response does not contain 'content' field")
        else:
            print("++++++++++++++++++++++++++++++++++++++")
            return response.content
            # raise ValueError(f"Unexpected response format: {type(response)}")
    except Exception as e:
        # Log the error and raise an HTTP exception
        # logger.error(f"AI processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")



    
@app.post("/query")
def handle_query(request: QueryRequest):
    """Fetch data from the database and process it with AI."""
    prompt = request.prompt
    logger.info(f"Received prompt: {prompt}")
    
    try:
        if "product" in request.prompt:
            # Fetch data from the database
            db_result = fetch_data_from_database()
            # logger.info(f"Fetched data: {db_result}")
            
            # Process the data with AI
            ai_result = process_data_with_ai(db_result,prompt)
            print("================================================")
        return ai_result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error handling query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error handling query: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
