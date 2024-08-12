from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import json
import re
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import openai

app = FastAPI()

csv_file_path = 'data.csv'
df = pd.read_csv(csv_file_path)

class ChatMessage(BaseModel):
    message: str

api_key = "sk-proj-V51XbVSuTtz09HVmjlhvT3BlbkFJjaYq0d6yOAICwiF3vxcj" 
llm = OpenAI(api_key=api_key)

prompt_template = PromptTemplate(
    input_variables=["message", "schema_info"],
    template="""
    You are a helpful assistant. The user has asked: '{message}'
    Generate a Pandas query to fetch the required sales data from the dataframe.
    The dataframe schema is as follows: {schema_info}
    Return only the query without any markdown or code block formatting.
    Example:
    user query: "give me sales details for product X"
    generated query: df[df['product'] == 'X']['sales']
    """
)
llm_chain = LLMChain(
    llm=llm,
    prompt=prompt_template
)

def get_schema_details():
    schema_info = {column: str(df[column].dtype) for column in df.columns}
    return schema_info

def execute_query(clean_query):
    try:
        result = eval(clean_query)
        data = result.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return data

@app.post("/chat/")
async def chat(message: ChatMessage):
    schema_details = get_schema_details()
    schema_info_str = json.dumps(schema_details, indent=2)

    try:
        response = llm_chain.run({
            "message": message.message,
            "schema_info": schema_info_str
        })
        clean_query = response.strip()
        results = execute_query(clean_query)
        return {"data": results}
    except openai.error.RateLimitError:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Chatbot is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
