import streamlit as st
import requests
import pandas as pd
import json
import matplotlib.pyplot as plt
import re

FASTAPI_URL = "http://localhost:8001/process-csv/"

st.title("AI Chatbot")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
query = st.text_input("Enter your query")

if st.button("Submit"):
    if uploaded_file is not None and query:
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            data = {"query": query}
            response = requests.post(FASTAPI_URL, files=files, data=data)

            if response.status_code == 200:
                st.success("AI Response:")
                response_data = response.json()

                # Display the text response
                st.markdown(response_data.get('response', 'No text response available'))

                # Extract and parse visualization details
                visualization_details_str = re.search(r'## Visualization_Details:\n\n```json\n(.*?)\n```', response_data.get('response', ''), re.DOTALL)
                if visualization_details_str:
                    visualization_details_str = visualization_details_str.group(1).strip()
                    # Clean and parse JSON string
                    cleaned_json_str = visualization_details_str.replace('\\n', '').replace('\\/', '/')
                    try:
                        visualization_details = json.loads(cleaned_json_str)
                        print(visualization_details)
                        # Check if visualization details are in the expected format
                        if not isinstance(visualization_details, dict):
                            st.warning("Invalid visualization details format.")
                        else:
                            x_label = visualization_details.get('x_axis', {}).get('label', 'X-axis')
                            y_label = visualization_details.get('y_axis', {}).get('label', 'Y-axis')
                            x_data = visualization_details.get('x_axis', {}).get('data', [])
                            y_data = visualization_details.get('y_axis', {}).get('data', [])

                            # Check if x_data and y_data are not empty
                            if x_data and y_data:
                                # Create a DataFrame
                                df = pd.DataFrame({x_label: x_data, y_label: y_data})

                                # Generate the bar chart
                                fig, ax = plt.subplots()
                                ax.bar(df[x_label], df[y_label])
                                ax.set_xlabel(x_label)
                                ax.set_ylabel(y_label)
                                ax.set_title("Company Revenue Over Time")

                                # Display the chart in Streamlit
                                st.pyplot(fig)
                            else:
                                st.warning("No data available for visualization.")
                    
                    except json.JSONDecodeError:
                        st.warning("Error decoding visualization details JSON.")
                else:
                    st.warning("No visualization details found in the response.")
                
            else:
                st.error(f"Error: {response.status_code}")
                st.write(response.json())
        except Exception as e:
            st.error(f"Error processing request: {str(e)}")
    else:
        st.warning("Please upload a CSV file and enter a query.")
