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

from ..tools.internet_search import internet_search


def calculate_how_many_schedules(state: OverallState, writer: StreamWriter):
    return {}
    print("\n>>> NODE: calculate_how_many_schedules")

    class FreeHourResponse(BaseModel):
        think_out_loud: str = Field(description="Think out loud your calculation")
        free_hours: int


    response = (
        ChatPromptTemplate.from_template(
            """
Calculate how many free hours I have when my trip schedule is like this. 

I'll be arriving at {trip_arrival_date} at {trip_arrival_time}. And I'm going to leave at {trip_departure_date} at {trip_departure_time}. I'm going to start my day at {trip_start_of_day_at}. And I'm going to end my day at {trip_end_of_day_at}.

I have some fixed schedules which you need to exclude from the calculation: {trip_fixed_schedules}

Before returning the result, think out loud on how you calculate the number of free hours.
"""
        )
        | chat_model.with_structured_output(FreeHourResponse)
    ).invoke(
        {
            "trip_arrival_date": state.trip_arrival_date,
            "trip_arrival_time": state.trip_arrival_time,
            "trip_departure_date": state.trip_departure_date,
            "trip_departure_time": state.trip_departure_time,
            "trip_start_of_day_at": state.trip_start_of_day_at,
            "trip_end_of_day_at": state.trip_end_of_day_at,
            "trip_fixed_schedules": state.trip_fixed_schedules,
        }
    )
    print("calculate_how_many_schedules: ", response)

    writer(
        {
            "title": f"Calculate that you have {response.free_hours} free hours",
            "description": response.think_out_loud,
        }
    )

    return {
        "trip_free_hours": response.free_hours,
    }


async def generate_queries(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: generate_queries")

    writer(
        {
            "role": Role.ReasoningStep.value,
            "message": "Reading your trip info and thinking what to look up on the internet",
        }
    )

    class Query(BaseModel):
        rationale: str
        query: str

    class Queries(BaseModel):
        queries: list[Query]

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


Okay, now it's your turn. Read the user's information that I provided in the beginning carefully, and generate upto {how_many_schedules} queries to look up information on the internet. Make sure each query don't overlap with the other ones.
"""
        )
        | chat_model.with_structured_output(Queries)
    ).invoke(
        {
            "user_name": state.user_name,
            "user_interests": state.user_interests,
            "user_extra_info": state.user_extra_info,
            "trip_arrival_date": state.trip_arrival_date,
            "trip_arrival_time": state.trip_arrival_time,
            "trip_arrival_terminal": state.trip_arrival_terminal,
            "trip_departure_date": state.trip_departure_date,
            "trip_departure_time": state.trip_departure_time,
            "trip_departure_terminal": state.trip_departure_terminal,
            "trip_start_of_day_at": state.trip_start_of_day_at,
            "trip_end_of_day_at": state.trip_end_of_day_at,
            "trip_location": state.trip_location,
            "trip_accomodation_location": state.trip_accomodation_location,
            "trip_budget": state.trip_budget,
            "trip_theme": state.trip_theme,
            "trip_fixed_schedules": state.trip_fixed_schedules,
            "how_many_schedules": (state.trip_free_hours or 30) // 10,  
        }
    )

    return [
        Send(n(internet_search), {**state.model_dump(), "query": query.query})
        for query in response.queries[:2]
    ]


def check_if_need_more_queries(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: check_if_need_more_queries")

    return {}


g = StateGraph(OverallState, input=InputState, output=OutputState)
g.add_edge(START, n(calculate_how_many_schedules))

g.add_node(n(calculate_how_many_schedules), calculate_how_many_schedules)
g.add_conditional_edges(
    n(calculate_how_many_schedules),
    generate_queries,
    [n(internet_search)],
)

g.add_node(n(internet_search), internet_search)
g.add_edge(n(internet_search), n(check_if_need_more_queries))


g.add_node(n(check_if_need_more_queries), check_if_need_more_queries)
g.add_edge(n(check_if_need_more_queries), END)
