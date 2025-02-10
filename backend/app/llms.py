import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatPerplexity

load_dotenv()

openai_chat_model = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY"),
)


perplexity_chat_model = ChatPerplexity(
    # model="sonar",
    # model="sonar-reasoning",
    model="llama-3.1-sonar-small-128k-online",
    temperature=0.7,
    pplx_api_key=os.getenv("PPLX_API_KEY"),
)
