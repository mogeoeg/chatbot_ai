from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_openai import ChatOpenAI, OpenAI

import io

app = FastAPI()

OPENAI_API_KEY = "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"

class QueryRequest(BaseModel):
    message: str

@app.post("/process-csv/")
async def process_csv(file: UploadFile, message: str = Form(...)):
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    contents = await file.read()
    csv_data = io.StringIO(contents.decode("utf-8"))
    agent = create_csv_agent(OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY), csv_data, verbose=True, allow_dangerous_code=True)

    try:
        out = agent.run(message+"give response like human friendly minimum 2 lines")
        return JSONResponse(content={'message': out})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
