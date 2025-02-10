import json
import datetime
from typing import TypedDict
from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field
from typing import Annotated, Any

from langgraph.graph import START, END, StateGraph, add_messages
from langgraph.types import StreamWriter, Command, Send

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    RemoveMessage,
)

from app.state import (
    OverallState,
    ScheduleItem,
    ScheduleItemType,
    ScheduleItemTime,
    extend_list,
)
from app.models import Role
from app.llms import openai_chat_model
from app.utils.utils import convert_schedule_items_to_string, calculate_empty_slots
from app.workflows.tools.internet_search import internet_search, InternetSearchState


MAX_NUM_OF_QUERIES = 3
MAX_NUM_OF_SCHEDULES = 100
MAX_NUM_OF_LOOPS = 100


def calculate_how_many_schedules(state: OverallState, writer: StreamWriter):
    return {"trip_free_hours": 40}

    print("\n>>> NODE: calculate_how_many_schedules")

    class FreeHourResponse(BaseModel):
        think_out_loud: str = Field(description="Think out loud your calculation")
        free_hours: int

    response: FreeHourResponse = (
        ChatPromptTemplate.from_template(
            """
Calculate how many free hours I have when my trip schedule is like this. 

I'll be arriving at {trip_arrival_date} at {trip_arrival_time}. And I'm going to leave at {trip_departure_date} at {trip_departure_time}. I'm going to start my day at {trip_start_of_day_at}. And I'm going to end my day at {trip_end_of_day_at}.

I have some fixed schedules which you need to exclude from the calculation: {trip_fixed_schedules}

Before returning the result, think out loud on how you calculate the number of free hours.
        """
        )
        | openai_chat_model.with_structured_output(FreeHourResponse)
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


def add_fixed_schedules(state: OverallState):
    print("\n>>> NODE: add_fixed_schedules")

    prompt = """Convert this into datetime input format [year, month, day, hour, minute].
    Arrival info: {trip_arrival_date} {trip_arrival_time}
    Departure info: {trip_departure_date} {trip_departure_time}""".format(
        **state.model_dump()
    )

    class TimeConvertOutput(BaseModel):
        arrival_time: str = Field(description="YYYY-MM-DD HH:MM")
        departure_time: str = Field(description="YYYY-MM-DD HH:MM")

    response: TimeConvertOutput = openai_chat_model.with_structured_output(
        TimeConvertOutput
    ).invoke(prompt)

    return {
        "schedule_list": [
            ScheduleItem(
                id=1,
                type=ScheduleItemType.TERMINAL,
                time=ScheduleItemTime(
                    start_time=response.arrival_time,
                    end_time=None,
                ),
                location="29 Broadway",
                title=f"Arrive to {state.trip_arrival_terminal}",
                description=None,
            ),
            ScheduleItem(
                id=2,
                type=ScheduleItemType.TERMINAL,
                time=ScheduleItemTime(
                    start_time=response.departure_time,
                    end_time=None,
                ),
                location="231 Broadway",
                title=f"Departure at {state.trip_departure_terminal}",
                description=None,
            ),
        ]
    }


def init_generate_queries_validation_loop(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: init_generate_queries_validation_loop")

    system_prompt = """
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
Query: Most active volcano in Iceland
    """.format(
        **state.model_dump()
    )

    return {
        "generate_query_loop_message_list": [SystemMessage(system_prompt)],
    }


class Query(BaseModel):
    id: int = Field(default=None)
    rationale: str
    content: str


# For the loop of generating queries and validating them
# We need an temporary state that stores the message list and the queries
class GenerateQueryLoopState(OverallState):
    loop_iteration: int = Field(default=0)
    generate_query_loop_message_list: Annotated[list[AnyMessage], extend_list] = Field(
        default_factory=list
    )
    generate_query_loop_queries: list[Query] = Field(default_factory=list)


async def generate_queries(state: GenerateQueryLoopState, writer: StreamWriter):
    print("\n>>> NODE: generate_queries")

    writer(
        {
            "description": "Reading your trip info and thinking what to look up on the internet",
        }
    )

    class Queries(BaseModel):
        queries: list[Query]

    response: Queries = (
        ChatPromptTemplate.from_messages(
            [
                *state.generate_query_loop_message_list,
                HumanMessage(
                    f"""Read my trip information carefully, and generate upto {state.trip_free_hours // 10} queries to look up information on the internet. Make sure each query don't overlap with the other ones."""
                ),
            ]
        )
        | openai_chat_model.with_structured_output(Queries)
    ).invoke({})

    response_dict_with_id = []
    for i, query in enumerate(response.queries):
        query_dict = query.model_dump()
        query_dict["id"] = i
        response_dict_with_id.append(query_dict)

    writer(
        {
            "title": "Queries to look up on the internet",
            "description": "\n".join([f"- {q.content}" for q in response.queries]),
        }
    )

    return {
        "generate_query_loop_message_list": [
            AIMessage(json.dumps(response_dict_with_id))
        ],
        "generate_query_loop_queries": response_dict_with_id,
        "loop_iteration": state.loop_iteration + 1,
    }


def validate_and_improve_queries(state: GenerateQueryLoopState, writer: StreamWriter):
    print("\n>>> NODE: validate_and_improve_queries")

    class ActionsType(str, Enum):
        ADD = "add"
        REMOVE = "remove"
        MODIFY = "modify"
        SKIP = "skip"

    class Actions(BaseModel):
        query_id: int
        rationale: str = Field(description="Explain why you want to do this action.")
        type: ActionsType
        new_query_value: str = Field(description="Leave empty if type is remove")

    class ValidateAndImproveQueries(BaseModel):
        is_current_queries_good_enough: bool = Field(description="")
        actions: list[Actions]

    response: ValidateAndImproveQueries = (
        ChatPromptTemplate.from_messages(
            [
                *state.generate_query_loop_message_list,
                HumanMessage(
                    "Check again if the queries are good enough. They should be diverse and not redundant. If there are redundant ones, remove them except the best one. Add new queries related to my trip infomation if they are not covered. Modify the queries if they are not specific enough to the my trip. For the queries that are good enough, put SKIP as an action type."
                ),
            ]
        )
        | openai_chat_model.with_structured_output(ValidateAndImproveQueries)
    ).invoke({})

    if (
        response.is_current_queries_good_enough
        or len(state.generate_query_loop_queries) >= MAX_NUM_OF_QUERIES
        or state.loop_iteration >= MAX_NUM_OF_LOOPS
    ):
        # If the current queries are good enough or the maximum number of queries has been reached, then terminate the loop and start the internet search nodes in parallel

        return Command(
            goto=[
                Send(
                    n(internet_search),
                    InternetSearchState.model_construct(
                        **state.model_dump(), query=query.content
                    ),
                )
                for query in state.generate_query_loop_queries
            ]
        )
    else:
        # Process actions to add, remove, and modify the queries
        queries = state.generate_query_loop_queries
        for action in response.actions:
            if action.type == ActionsType.ADD:
                # Add a new query with the next available ID
                if len(queries) == 0:
                    next_id = 1
                else:
                    # Find the highest ID to assign next ID
                    next_id = max([q.id for q in queries], default=0) + 1
                new_query = Query(
                    id=next_id,
                    rationale=action.rationale,
                    content=action.new_query_value,
                )
                queries.append(new_query)
            elif action.type == ActionsType.REMOVE:
                # Remove query by ID
                queries[:] = [q for q in queries if q.id != action.query_id]
            elif action.type == ActionsType.MODIFY:
                # Modify existing query by ID
                for query in queries:
                    if query.id == action.query_id:
                        query.content = action.new_query_value
                        break

        writer(
            {
                "title": "Validation result",
                "description": "\n".join(
                    [
                        f"- {action.rationale} / {action.type.value} query with id {action.query_id} -> {action.new_query_value}"
                        for action in response.actions
                        if action.type != ActionsType.SKIP
                    ]
                ),
            }
        )

        writer(
            {
                "title": "Improved queries",
                "description": "\n".join([f"- {q.content}" for q in queries]),
            }
        )

        # Create a new message that contains the LLM's actions
        new_message = AIMessage(
            "\n".join([json.dumps(action.model_dump()) for action in response.actions])
        )

        # Update GenerateQueryLoopState with new queries and a message, and loop back to the current node "validate_and_improve_queries"
        return Command(
            update={
                "generate_query_loop_message_list": [new_message],
                "generate_query_loop_queries": queries,
                "loop_iteration": state.loop_iteration + 1,
            },
            goto=n(validate_and_improve_queries),
        )


def init_slot_in_schedule_loop(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: init_slot_in_schedule_loop")

    format_data = state.model_dump()
    format_data["internet_search_results_string"] = "\n\n".join(
        [
            f"Search Query:{r['query']}\nResult:{r['query_result']}"
            for r in state.internet_search_result_list
        ]
    )
    format_data["schedule_string"] = convert_schedule_items_to_string(
        state.schedule_list
    )

    system_prompt = SystemMessage(
        """
You are an AI tour planner. You are going to arrange a schedule for a user's trip. 

Here are some details about the trip:

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


Here are information that you have collected on the internet:
{internet_search_results_string}


---


Here are the current items in the schedule:
{schedule_string}


---


You can add, modify, or remove items in the schedule. 
    """.format(
            **format_data
        )
    )

    return {
        "system_prompt": system_prompt,
    }


class SlotInScheduleState(OverallState):
    system_prompt: SystemMessage
    slot_in_schedule_loop_messages: Annotated[list[AnyMessage], add_messages] = Field(
        default_factory=list
    )


def slot_in_schedule(state: SlotInScheduleState, writer: StreamWriter):
    if len(state.schedule_list) >= MAX_NUM_OF_SCHEDULES:
        print("\n>>> Terminate slot_in_schedule")
        return Command(
            goto="__end__",
        )

    print("\n>>> NODE: slot_in_schedule")

    messages = state.slot_in_schedule_loop_messages
    should_add_system_prompt = False
    if len(messages) == 0:
        should_add_system_prompt = True
        messages.append(state.system_prompt)

    # Add system prompt for the first iteration

    human_message_asking_next_action = HumanMessage(
        f"Slot an item in the empty schedule.\n\nEmpty slots:{calculate_empty_slots(state.schedule_list, state.trip_start_of_day_at, state.trip_end_of_day_at)}"
    )

    messages.append(human_message_asking_next_action)

    class SlotInScheduleAction(BaseModel):
        reasining_stage: str = Field(
            description="Before creating the schedule item, think out loud your reasoning behind this action."
        )
        schedule_item: ScheduleItem

    response: SlotInScheduleAction = (
        ChatPromptTemplate.from_messages(messages)
        | openai_chat_model.with_structured_output(SlotInScheduleAction)
    ).invoke({})

    writer(
        {
            "title": convert_schedule_items_to_string([response.schedule_item]),
            "description": response.reasining_stage,
        }
    )

    new_messages = []
    if should_add_system_prompt:
        new_messages.append(state.system_prompt)
    new_messages.extend(
        [
            human_message_asking_next_action,
            AIMessage(response.schedule_item.model_dump_json()),
        ]
    )

    return Command(
        goto=n(slot_in_schedule),
        update={
            "slot_in_schedule_loop_messages": new_messages,
            "schedule_list": [response.schedule_item],
        },
    )


g = StateGraph(OverallState)
g.add_edge(START, n(calculate_how_many_schedules))

g.add_node(n(calculate_how_many_schedules), calculate_how_many_schedules)
g.add_edge(n(calculate_how_many_schedules), n(add_fixed_schedules))

g.add_node(n(add_fixed_schedules), add_fixed_schedules)
g.add_edge(n(add_fixed_schedules), n(init_generate_queries_validation_loop))

g.add_node(
    n(init_generate_queries_validation_loop), init_generate_queries_validation_loop
)
g.add_edge(n(init_generate_queries_validation_loop), n(generate_queries))

g.add_node(n(generate_queries), generate_queries)
g.add_edge(n(generate_queries), n(validate_and_improve_queries))

g.add_node(n(validate_and_improve_queries), validate_and_improve_queries)

g.add_node(n(internet_search), internet_search)
g.add_edge(n(internet_search), n(init_slot_in_schedule_loop))

g.add_node(n(init_slot_in_schedule_loop), init_slot_in_schedule_loop)
g.add_edge(n(init_slot_in_schedule_loop), n(slot_in_schedule))

g.add_node(n(slot_in_schedule), slot_in_schedule)
