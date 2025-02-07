from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field

from langgraph.graph import START, END, StateGraph
from langgraph.types import StreamWriter, Command, Send

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableParallel


from app.state import OverallState, InputState, OutputState
from app.llm import chat_model

from app.models import Role

from ..tools.internet_search import tavily_search


def calculate_how_many_schedules(state: OverallState):
    print("\n>>> NODE: calculate_how_many_schedules")

    total_wake_time = state


async def generate_queries(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: generate_queries")

    writer(
        {
            "role": Role.ReasoningStep.value,
            "message": "Reading your trip info and thinking what to look up on the internet",
        }
    )

    class Query(BaseModel):
        rationale: str = Field(..., description="Rationale for the query")
        query: str = Field(..., description="The query to be executed")

    class Queries(BaseModel):
        queries: list[Query] = Field(..., description="The queries to be executed")

    response = await (
        ChatPromptTemplate.from_template(
            """
You are an AI tour planner doing some research for the user.


The user will be visiting {trip_location} during {trip_duration}. The budget is {trip_budget} and the user wants the trip to be a theme of {trip_theme}. The user's interests are {user_interests}. 

- The user's transportation schedule is the following:
{trip_transportation_schedule}
- There are fixed schedules that the user has to follow: 
{trip_fixed_schedules}
- Extra information about the user: 
{user_extra_info}


---


With this information, you are going to do some research on the internet. Here are some examples for diverse trip scenarios:

1. 
Rationale: The user is visiting Quebec City and wants a Cultural & Heritage theme trip. I should look up if there is any museum related to indigenous culture in Quebec City. I should also check if the museum is open during the duration of the trip.
Query: Museums related to indigenous culture in Quebec City.
Condition: Open during September 2 to 4.

2.
Rationale: The user is visiting Cuba and wants a Relaxation & Wellness theme trip. I should look up which beach is the best to rest in Cuba.
Query: Best beaches in Cuba to relax

3.
Rationale: The user is visiting Iceland and wants a Adventure & Sports theme trip. I should look up which volcano is the most active in Iceland.
Query: Most active volcano in Iceland


---


Okay, now it's your turn. Read the user's information that I provided in the beginning carefully, and generate up to 10 queries to look up information on the internet. Make sure each query don't overlap with the other ones.
"""
        )
        | chat_model.with_structured_output(Queries)
    ).ainvoke(
        {
            "user_name": state.user_name,
            "user_interests": state.user_interests,
            "user_extra_info": state.user_extra_info,
            "trip_transportation_schedule": state.trip_transportation_schedule,
            "trip_location": state.trip_location,
            "trip_duration": state.trip_duration,
            "trip_budget": state.trip_budget,
            "trip_theme": state.trip_theme,
            "trip_fixed_schedules": state.trip_fixed_schedules,
        }
    )

    return {
        "queries_for_internet_search": [query.query for query in response.queries]
    }

def check_if_need_more_queries(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: check_if_need_more_queries")

    return {

    }


g = StateGraph(OverallState, input=InputState, output=OutputState)
g.add_edge(START, n(calculate_how_many_schedules))

g.add_node(n(calculate_how_many_schedules), calculate_how_many_schedules)
g.add_edge(n(calculate_how_many_schedules), n(generate_queries))

g.add_node(n(generate_queries), generate_queries)
g.add_edge(n(generate_queries), n(tavily_search))

g.add_node(n(tavily_search), tavily_search)
g.add_edge(n(tavily_search), n(check_if_need_more_queries))


g.add_node(n(check_if_need_more_queries), check_if_need_more_queries)
g.add_edge(n(check_if_need_more_queries), END)
