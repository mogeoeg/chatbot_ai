from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
import io

app = FastAPI()

client = ChatGoogleGenerativeAI(
    api_key='AIzaSyA7qBvXge6Ss6_D8SMAK982C1cT3ZfZgjM',
    model='gemini-1.5-flash',
    convert_system_message_to_human=True
)

@app.post("/process-csv/")
async def process_csv(
    file: UploadFile = File(...), 
    query: str = Form(...)
):
    print("yes")
    allowed_content_types = ['text/csv', 'application/vnd.ms-excel']
    print(file.content_type)
    if file.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        data_json = df.to_json(orient='records')
        messages = [
            SystemMessage(content=(
                "You are a helpful assistant and data analyst. Process the following data and provide two types of responses:\n\n"
                "1. **Text Response:** Answer the following questions based on the data provided. Make sure the response is insightful and human-like.\n"
                "2. **Visualization_Details:** Describe the x-axis and y-axis data that would be used to generate a meaningful bar chart based on the data provided as json. "
                "Ensure the description includes the labels for both axes and the data points. If the data is not available, describe the chart as being black with no data.\n\n"
                "Here is the data you need to analyze:\n\n"
                "{data_json}\n\n"
                "Here is the query you need to answer:\n\n"
                "{query}\n\n"
                "For the visualization, provide the x-axis labels, y-axis labels, and data points in JSON format. Then, provide Streamlit code that will generate the bar chart based on this data. "
                "If no data is available, provide code that generates a completely black image."
            )),
            HumanMessage(content=f"Process this data: {data_json} and answer the following questions: {query}. "
                                "Describe the chart data and provide the Streamlit code for generating the bar chart.")
        ]




        response = client.invoke(input=messages)
        return {"response": response.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

