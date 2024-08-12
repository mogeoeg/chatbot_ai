import time
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from openai import RateLimitError, AuthenticationError
import backoff

app = FastAPI()

text_template_cg = """
As a digital marketer specialized in content generation, please create a 500-words blog post on the following content description:

Content Description: {contentDescription}

To ensure a cohesive structure, please use the following content template:

1st paragraph: Start with a captivating introduction that grabs the reader's attention and provides an overview of the topic.

2nd paragraph: Develop the content in a logical and organized manner, providing valuable information, insights, and examples related to the content description. Break the body into several paragraphs to enhance readability and flow.

3rd paragraph: Summarize the main points discussed in the body and provide a closing thought or call to action to engage the reader further.

Hashtags: Add at least 5 hashtags related to the content generated.

After creating the content, include five relevant hashtags at the end that are related to the content.

Remember to maintain a professional and informative tone throughout the blog post.

Blog post with hashtags:
"""

text_prompt_cg = PromptTemplate(template=text_template_cg, input_variables=["contentDescription"])

try:
    text_model_cg = ChatOpenAI(
        model="gpt-3.5-turbo-1106",
        openai_api_key="sk-proj-hNwk8z133MQNT32OiVF5T3BlbkFJQ0qpaQzkED6boVjQm7Pw",
        temperature=0.8,
        max_tokens=3056
    )
except AuthenticationError:
    raise HTTPException(status_code=500, detail="Invalid OpenAI API key")

text_chain_cg = LLMChain(prompt=text_prompt_cg, llm=text_model_cg)

class BlogPostInput(BaseModel):
    contentDescription: str

def on_backoff(details):
    print(f"Backing off {details['wait']:0.1f} seconds after {details['tries']} tries")

def should_retry(exception):
    return isinstance(exception, RateLimitError)

@backoff.on_exception(
    backoff.expo,
    RateLimitError,
    max_tries=5,
    max_time=300,
    on_backoff=on_backoff,
    giveup=lambda e: not should_retry(e)
)
def generate_blog_post_with_backoff(content_description):
    return text_chain_cg.run(contentDescription=content_description)

def fallback_generation(content_description):
    return f"Unable to generate a full blog post at this time due to API limitations. Here's a summary of your topic: {content_description}"

@app.post("/generate-blog-post")
async def generate_blog_post(input: BlogPostInput):
    try:
        response = generate_blog_post_with_backoff(input.contentDescription)
        return {"blog_post": response}
    except RateLimitError:
        fallback_response = fallback_generation(input.contentDescription)
        return {"blog_post": fallback_response, "note": "Generated using fallback method due to API limitations."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)