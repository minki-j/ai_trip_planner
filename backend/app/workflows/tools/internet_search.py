from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field

from langgraph.types import StreamWriter, Command

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from app.state import OverallState, InputState
from app.llms import perplexity_chat_model


class InternetSearchState(InputState):
    query: str = Field(description="The query to search for.")


def internet_search(state: InternetSearchState, writer: StreamWriter):
    print("\n>>> NODE: internet_search")

    #! Excluded trip_theme, user_interests, and extra_info since it distracts from the task
    prompt = """
You are an AI tour planner doing some research for the user.

The user will be visiting {trip_location}, staying at {trip_accommodation_location}, from {trip_arrival_date}  {trip_arrival_time} to {trip_departure_date}  {trip_departure_time}. They prefer a {trip_budget} trip and plan to start their day at {trip_start_of_day_at} and end it at {trip_end_of_day_at}.


---


Now here is your task: Collect information about the following query.
{query}


---


Important Rules
- Keep in mind the user's trip information, and sort the results in a way that the most relevant information is at the top.
- You don't need to plan the full schedule, just collect information about the query.
- Make sure only include information that is available from {trip_arrival_date} {trip_arrival_time} to {trip_departure_date} {trip_departure_time}.
- Do not include citations.
- If possible (without making anything up), include practical tips for each tour recommendation, such as signature dishes to order, best photo spots, ways to get cheaper or easier tickets, best times to avoid crowds, portion sizes to expect, local customs or etiquette to be aware of, transportation tips, weather considerations, common scams or tourist traps to avoid, and unique souvenirs to look for.
    """.format(
        **state.model_dump()
    )

    response = (perplexity_chat_model | StrOutputParser()).invoke(prompt)

    writer(
        {
            "title": f"{state.query}",
            "description": response,
        }
    )

    result = {
        "query": state.query,
        "query_result": response,
    }

    return {"internet_search_result_list": [result]}
