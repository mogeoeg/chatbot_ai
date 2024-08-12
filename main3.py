import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
import google.generativeai as genai
import pandas as pd
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
api_key = "AIzaSyDzARgIWrFbTtg4lkbdSwXTRUX_RFdzAMM"
# api_key = "AIzaSyA7qBvXge6Ss6_D8SMAK982C1cT3ZfZgjM"
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

def clean_text(text):
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

@app.post("/chat/")
async def chat(message: str = Form(...), file: UploadFile = File(...)):
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        raise HTTPException(status_code=400, detail="Invalid CSV file")
    csv_data_json = df.to_json(orient='records')
    prompt = f"""
    You are a helpful assistant. The user has asked:
    '{message}'
    Generate a response based on the CSV file's data and the user's query.
    The CSV data is as follows:
    {csv_data_json}
    If the name is not unique, get all of the ages associated with that name.
    Compare the data like who is best customer based having details
    Predict the income
    """

    try:
        response = model.generate_content([prompt], generation_config=generation_config, safety_settings=safety_settings)
        logger.info(f"Response from model: {response}")
        
        response_text = response._result.candidates[0].content.parts[0].text
        response_text = clean_text(response_text)

    except AttributeError as e:
        logger.error(f"Error extracting response text: {e}")
        response_text = "There was an error processing the response from the model."

    return {"response": response_text}

@app.get("/")
async def root():
    return {"message": "Chatbot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
