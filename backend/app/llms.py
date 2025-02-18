import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatPerplexity


load_dotenv()

chat_model_anthropic_first = ChatAnthropic(
    model="claude-3-5-sonnet-latest",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0.5,
).with_fallbacks(
    [
        ChatAnthropic(
            model="claude-3-5-sonnet-latest",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1,  # lower the temperature
        ),
        ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),  # try with gpt-4o
        ChatOpenAI(
            model_name="o3-mini",
            temperature=None,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),  # try with o3-mini
    ]
)

chat_model_openai_first = ChatOpenAI(
    model_name="o3-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.5,
).with_fallbacks(
    [
        ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        ChatAnthropic(
            model="claude-3-5-sonnet-latest",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1,
        ),
        ChatOpenAI(
            model_name="o3-mini",
            temperature=None,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
    ]
)


reasoning_model = ChatOpenAI(
    model_name="o3-mini",
    temperature=None,
    api_key=os.getenv("OPENAI_API_KEY"),
).with_fallbacks(
    [
        ChatOpenAI(
            model_name="o3-mini",
            temperature=None,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),  # try one more time
    ]
)


perplexity_chat_model = ChatPerplexity(
    model="sonar",
    # model="sonar-reasoning",
    # model="llama-3.1-sonar-small-128k-online",
    temperature=0.7,
    pplx_api_key=os.getenv("PPLX_API_KEY"),
)  # no fallbacks are required since it doesn't have structured outputs


small_model_for_summarization = ChatAnthropic(
    model_name="claude-3-5-haiku-latest",
    temperature=0.7,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
).with_fallbacks(
    [
        ChatAnthropic(
            model="claude-3-5-haiku-latest",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.1,  # lower the temperature
        ),
        ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),  # try with gpt-4o mini
    ]
)
