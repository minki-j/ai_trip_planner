from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field

from langgraph.types import StreamWriter, Command

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from app.state import OverallState

from app.llm import perplexity_chat_model



def internet_search(state: dict, writer: StreamWriter):
    print("\n>>> NODE: internet_search")

    writer(
        {
            "title": f"Searching the web for {state['query']}",
            "description": "It might take some time...",
        }
    )

    response = (
        ChatPromptTemplate.from_template(
            """
You are an AI tour planner doing some research for the user.

The user will be visiting {trip_location} (staying at {trip_accomodation_location}). The budget is {trip_budget} and the user wants the trip to be a theme of {trip_theme}. The user's interests are {user_interests}. 

- The user's arrival details:
  Date: {trip_arrival_date}
  Time: {trip_arrival_time}
  Terminal: {trip_arrival_terminal}

- The user's departure details:
  Date: {trip_departure_date}
  Time: {trip_departure_time}
  Terminal: {trip_departure_terminal}

- Daily schedule:
  Start of day: {trip_start_of_day_at}
  End of day: {trip_end_of_day_at}

- There are fixed schedules that the user has to follow:
{trip_fixed_schedules}

- Extra information about the user:
{user_extra_info}


---

Now, collect information about the following query: 
{query}

Keep in mind the user's trip information, and sort the results in a way that the most relevant information is at the top.
"""
        )
        | perplexity_chat_model
        | StrOutputParser()
    ).invoke(
        {
            "user_interests": state["user_interests"],
            "user_extra_info": state["user_extra_info"],
            "trip_arrival_date": state["trip_arrival_date"],
            "trip_arrival_time": state["trip_arrival_time"],
            "trip_arrival_terminal": state["trip_arrival_terminal"],
            "trip_departure_date": state["trip_departure_date"],
            "trip_departure_time": state["trip_departure_time"],
            "trip_departure_terminal": state["trip_departure_terminal"],
            "trip_start_of_day_at": state["trip_start_of_day_at"],
            "trip_end_of_day_at": state["trip_end_of_day_at"],
            "trip_location": state["trip_location"],
            "trip_accomodation_location": state["trip_accomodation_location"],
            "trip_budget": state["trip_budget"],
            "trip_theme": state["trip_theme"],
            "trip_fixed_schedules": state["trip_fixed_schedules"],
            "query": state["query"],
        }
    )

    print("internet_search result: ", response)

    writer(
        {
            "title": f"Internet search result for {state['query']}",
            "description": response,
        }
    )

    result = {
        "query": state["query"],
        "query_result": response,
    }

    return {"internet_search_results": [result]}
