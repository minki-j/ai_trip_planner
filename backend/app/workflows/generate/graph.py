import json
import datetime
from typing import TypedDict
from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field
from typing import Annotated, Any

from langgraph.graph import START, END, StateGraph
from langgraph.types import StreamWriter, Command, Send

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableParallel


from app.state import (
    OverallState,
    extend_list,
    ScheduleItem,
    ScheduleItemType,
    TimeSlot,
)
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


def add_terminal_time_to_schedule(state: OverallState):
    print("\n>>> NODE: add_terminal_time_to_schedule")

    prompt = f"""Convert this into datetime input format [year, month, day, hour, minute].
    Arrival info: {state.trip_arrival_date} {state.trip_arrival_time}
    Departure info: {state.trip_departure_date} {state.trip_departure_time}"""

    class TimeConvertOutput(BaseModel):
        arrival_time: list[int]
        departure_time: list[int]

    response = chat_model.with_structured_output(TimeConvertOutput).invoke(prompt)

    arrival_time = datetime.datetime(*response.arrival_time)
    departure_time = datetime.datetime(*response.departure_time)

    return {
        "schedule": [
            ScheduleItem(
                id=1,
                type=ScheduleItemType.TERMINAL,
                time=TimeSlot(
                    start_time=arrival_time,
                    end_time=None,
                ),
                location="29 Broadway",
                title=f"Arrive to {state.trip_arrival_terminal}",
                description=None,
            ),
            ScheduleItem(
                id=2,
                type=ScheduleItemType.TERMINAL,
                time=TimeSlot(
                    start_time=departure_time,
                    end_time=None,
                ),
                location="231 Broadway",
                title=f"Departure at {state.trip_departure_terminal}",
                description=None,
            )
        ]
    }


def init_generate_queries_validation_loop(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: init_generate_queries_validation_loop")

    system_prompt = """You are an AI tour planner doing some research for the user.

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


With this information, you are going to do some research on the internet. Here are example outputs:

1. 
Rationale: The user is visiting Quebec City and wants a Cultural & Heritage theme trip. I should look up if there is any museum related to indigenous culture in Quebec City. I should also check if the museum is open during the duration of the trip.
Query: Museums related to indigenous culture in Quebec City.
Condition: Open during September 2 to 4.

2.
Rationale: The user is visiting Cuba and wants a Relaxation & Wellness theme trip. I should look up which beach is the best to rest in Cuba.
Query: Best beaches in Cuba to relax

3.
Rationale: The user is visiting Iceland and wants a Adventure & Sports theme trip. I should look up which volcano is the most active in Iceland.
Query: Most active volcano in Iceland""".format(
        user_name=state.user_name,
        user_interests=state.user_interests,
        user_extra_info=state.user_extra_info,
        trip_arrival_date=state.trip_arrival_date,
        trip_arrival_time=state.trip_arrival_time,
        trip_arrival_terminal=state.trip_arrival_terminal,
        trip_departure_date=state.trip_departure_date,
        trip_departure_time=state.trip_departure_time,
        trip_departure_terminal=state.trip_departure_terminal,
        trip_start_of_day_at=state.trip_start_of_day_at,
        trip_end_of_day_at=state.trip_end_of_day_at,
        trip_location=state.trip_location,
        trip_accomodation_location=state.trip_accomodation_location,
        trip_budget=state.trip_budget,
        trip_theme=state.trip_theme,
        trip_fixed_schedules=state.trip_fixed_schedules,
    )

    return {
        "message_list": [AIMessage(system_prompt)],
    }


class Query(BaseModel):
    id: int = Field(default=None)
    rationale: str
    query: str


class LoopState(OverallState):
    message_list: Annotated[list[AnyMessage], extend_list] = Field(default_factory=list)
    queries: list[Query] = Field(default_factory=list)


async def generate_queries(state: LoopState, writer: StreamWriter):
    print("\n>>> NODE: generate_queries")

    writer(
        {
            "description": "Reading your trip info and thinking what to look up on the internet",
        }
    )

    class Queries(BaseModel):
        queries: list[Query]

    response = (
        ChatPromptTemplate.from_messages(
            [
                *state.message_list,
                HumanMessage(
                    f"""Read my trip information carefully, and generate upto {(state.trip_free_hours or 30) // 10} queries to look up information on the internet. Make sure each query don't overlap with the other ones."""
                ),
            ]
        )
        | chat_model.with_structured_output(Queries)
    ).invoke({})

    response_dict_with_id = []
    for i, query in enumerate(response.queries):
        query_dict = query.model_dump()
        query_dict["id"] = i
        response_dict_with_id.append(query_dict)

    writer(
        {
            "title": "Queries to look up on the internet",
            "description": "\n".join([f"- {q.query}" for q in response.queries]),
        }
    )

    return {
        "message_list": [AIMessage(json.dumps(response_dict_with_id))],
        "queries": response_dict_with_id,
    }


def validate_and_improve_queries(state: LoopState, writer: StreamWriter):
    print("\n>>> NODE: validate_and_improve_queries")

    class ActionsType(str, Enum):
        ADD = "add"
        REMOVE = "remove"
        MODIFY = "modify"
        SKIP = "skip"

    class Actions(BaseModel):
        rationale: str = Field(description="Explain why you want to do this action")
        type: ActionsType
        query_id: int
        new_query_value: str = Field(description="Leave empty if type is remove")

    class ValidateAndImproveQueries(BaseModel):
        is_current_queries_good_enough: bool = Field(description="")
        actions: list[Actions]

    response = (
        ChatPromptTemplate.from_messages(
            [
                *state.message_list,
                HumanMessage(
                    "Check again if the queries are good enough. They should be diverse and not redundant. If there are redundant ones, remove them except the best one. Add new queries related to my trip infomation if they are not covered. Modify the queries if they are not specific enough to the my trip. If a query is good enough, skip it."
                ),
            ]
        )
        | chat_model.with_structured_output(ValidateAndImproveQueries)
    ).invoke({})

    if response.is_current_queries_good_enough or len(state.queries) >= 5:
        return Command(
            goto=[
                Send(n(internet_search), {**state.model_dump(), "query": query.query})
                for query in state.queries[:]
            ]
        )
    else:
        queries = state.queries
        for action in response.actions:
            if action.type == ActionsType.ADD:
                if len(queries) == 0:
                    next_id = 1
                else:
                    # Find the highest ID to assign next ID
                    next_id = max([q.id for q in queries], default=0) + 1
                new_query = Query(
                    id=next_id,
                    rationale=action.rationale,
                    query=action.new_query_value,
                )
                queries.append(new_query)
            elif action.type == ActionsType.REMOVE:
                # Find and remove query by ID
                queries[:] = [q for q in queries if q.id != action.query_id]
            elif action.type == ActionsType.MODIFY:
                # Find and modify query by ID
                for query in queries:
                    if query.id == action.query_id:
                        query.query = action.new_query_value
                        break

        writer(
            {
                "title": "Validation result",
                "description": "\n".join(
                    [
                        f"- **Action:** {action.type.value} // **Rationale:** {action.rationale} // **New query:** {action.new_query_value}"
                        for action in response.actions
                        if action.type != ActionsType.SKIP
                    ]
                ),
            }
        )

        writer(
            {
                "title": "Improved queries",
                "description": "\n".join([f"- {q.query}" for q in queries]),
            }
        )

        return Command(
            update={
                "message_list": [
                    AIMessage(
                        "\n".join(
                            [
                                json.dumps(action.model_dump())
                                for action in response.actions
                            ]
                        )
                    )
                ],
                "queries": queries,
            },
            goto=n(validate_and_improve_queries),
        )


g = StateGraph(OverallState)
g.add_edge(START, n(calculate_how_many_schedules))

g.add_node(n(calculate_how_many_schedules), calculate_how_many_schedules)
g.add_edge(n(calculate_how_many_schedules), n(add_terminal_time_to_schedule))

g.add_node(n(add_terminal_time_to_schedule), add_terminal_time_to_schedule)
g.add_edge(n(add_terminal_time_to_schedule), n(init_generate_queries_validation_loop))

g.add_node(
    n(init_generate_queries_validation_loop), init_generate_queries_validation_loop
)
g.add_edge(n(init_generate_queries_validation_loop), n(generate_queries))

g.add_node(n(generate_queries), generate_queries)
g.add_edge(n(generate_queries), n(validate_and_improve_queries))

g.add_node(n(validate_and_improve_queries), validate_and_improve_queries)

g.add_node(n(internet_search), internet_search)
