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
from app.llms import chat_model
from app.utils.utils import convert_schedule_items_to_string, calculate_empty_slots
from app.workflows.tools.internet_search import internet_search, InternetSearchState


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


def add_terminal_schedules(state: OverallState):
    print("\n>>> NODE: add_terminal_schedules")

    arrival_time = f"{state.trip_arrival_date} {state.trip_arrival_time}"
    departure_time = f"{state.trip_departure_date} {state.trip_departure_time}"

    return {
        "schedule_list": [
            ScheduleItem(
                id=1,
                type=ScheduleItemType.TERMINAL,
                time=ScheduleItemTime(
                    start_time=arrival_time,
                    end_time=None,
                ),
                location=state.trip_arrival_terminal,
                title=f"Arrive at {state.trip_arrival_terminal}",
                description=None,
                suggestion=None,
            ),
            ScheduleItem(
                id=2,
                type=ScheduleItemType.TERMINAL,
                time=ScheduleItemTime(
                    start_time=departure_time,
                    end_time=None,
                ),
                location=state.trip_departure_terminal,
                title=f"Departure at {state.trip_departure_terminal}",
                description=None,
                suggestion=None,
            ),
        ]
    }


def add_fixed_schedules(state: OverallState):
    if not state.trip_fixed_schedules:
        print("\n>>> SKIP: add_fixed_schedules (No fixed schedules provided)")
        return {}
    print("\n>>> NODE: add_fixed_schedules")

    # check all fixed schedules are type of ScheduleItem
    if not all(isinstance(s, ScheduleItem) for s in state.trip_fixed_schedules):
        raise ValueError(
            "Invalid fixed schedules provided. They must be a list of ScheduleItem."
        )

    return {"schedule_list": state.trip_fixed_schedules}


def init_generate_queries_validation_loop(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: init_generate_queries_validation_loop")

    format_data = state.model_dump()
    format_data["trip_fixed_schedules_string"] = convert_schedule_items_to_string(
        state.trip_fixed_schedules, include_ids=False
    )

    system_prompt = """
As an AI tour planner, you research travel options by performing internet searches to gather current information for a user.

The user will be visiting {trip_location}, staying at {trip_accommodation_location}, from {trip_arrival_date} {trip_arrival_time} to {trip_departure_date} {trip_departure_time}. They prefer a {trip_budget} trip with a focus on {trip_theme} and are particularly interested in {user_interests}. Their day starts at {trip_start_of_day_at} and ends at {trip_end_of_day_at}.

There are fixed schedules that the user has to follow:
{trip_fixed_schedules_string}

Extra information about the user:
{user_extra_info}


---


Here are examples of queries that you should generate. Each example is based on different trip scenario which are not included here. For the queries that you are going to generate, you should use the trip information provided above. 

1. 
Rationale: The user is visiting Quebec City and wants a Cultural & Heritage theme trip. I should look up if there is any museum related to indigenous culture in Quebec City. I should also check if the museum is open during the duration of the trip.
Query: Museums related to indigenous culture in Quebec City


2.
Rationale: The user is visiting Cuba and wants a Relaxation & Wellness theme trip. I should look up which beach is the best to rest in Cuba.
Query: Best beaches in Cuba to relax

3.
Rationale: The user is visiting Iceland and wants a Adventure & Sports theme trip. I should look up which volcano is the most active in Iceland.
Query: Most active volcano in Iceland


---


Important notes:
- You do not need to include the trip information in your queries. For instance, you do not need to specify the time that the user is visiting the location.
    """.format(
        format_data
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

    class Queries(BaseModel):
        queries: list[Query]

    human_message = HumanMessage(
        f"""Read my trip information carefully, and generate upto {state.trip_free_hours // 10} queries to look up information on the internet. Make sure each query don't overlap with the other ones."""
    )
    state.generate_query_loop_message_list.append(human_message)

    response: Queries = (
        ChatPromptTemplate.from_messages(state.generate_query_loop_message_list)
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
            "description": "\n".join([f"- {q.content}" for q in response.queries]),
        }
    )

    return {
        "generate_query_loop_message_list": [
            human_message,
            AIMessage(json.dumps(response_dict_with_id)),
        ],
        "generate_query_loop_queries": response_dict_with_id,
        "loop_iteration": state.loop_iteration + 1,
    }


def validate_and_improve_queries_loop(
    state: GenerateQueryLoopState, writer: StreamWriter
):
    print("\n>>> NODE: validate_and_improve_queries_loop")

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
        is_current_queries_good_enough: bool = Field(
            description="All queries meet the criteria."
        )
        actions: list[Actions] = Field(
            description="if is_current_queries_good_enough is True, leave this empty."
        )

    human_message = HumanMessage(
        "Review the queries for quality. Ensure they are diverse and not redundant. If any queries are redundant, keep only the best one. Add new queries relevant to my trip if any key aspects are missing. Modify queries that are too vague to make them more specific to my trip. For queries that meet the criteria, mark them with 'SKIP' as the action type. If all queries are good enough, return True for is_current_queries_good_enough."
    )

    state.generate_query_loop_message_list.append(human_message)

    response: ValidateAndImproveQueries = (
        ChatPromptTemplate.from_messages(state.generate_query_loop_message_list)
        | chat_model.with_structured_output(ValidateAndImproveQueries)
    ).invoke({})

    if (
        response.is_current_queries_good_enough
        or len(state.generate_query_loop_queries) >= state.trip_free_hours // 10
        or state.loop_iteration >= MAX_NUM_OF_LOOPS
    ):
        # If the current queries are good enough or the maximum number of queries has been reached, then terminate the loop and start the internet search nodes in parallel
        return Command(
            goto=[
                Send(
                    n(internet_search),
                    InternetSearchState.model_validate(
                        {
                            **state.model_dump(),
                            "query": query.content,
                        }
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
                "generate_query_loop_message_list": [human_message, new_message],
                "generate_query_loop_queries": queries,
                "loop_iteration": state.loop_iteration + 1,
            },
            goto=n(validate_and_improve_queries_loop),
        )


def init_slot_in_schedule_loop(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: init_slot_in_schedule_loop")

    format_data = state.model_dump()
    format_data["internet_search_results_string"] = "\n\n\n".join(
        [
            f"#{i+1}.\n\n##Search Query: {r['query']}\n\n##Result: {r['query_result'].replace("---", "")}"
            for i, r in enumerate(state.internet_search_result_list)
        ]
    )
    format_data["schedule_string"] = convert_schedule_items_to_string(
        state.schedule_list
    )

    system_prompt = SystemMessage(
        """
As an AI tour planner, you help arrange travel schedules for users' trips. 

The user will be visiting {trip_location}, staying at {trip_accommodation_location}, from {trip_arrival_date} {trip_arrival_time} to {trip_departure_date} {trip_departure_time}. They prefer a {trip_budget} trip with a focus on {trip_theme} and are particularly interested in {user_interests}. Their day starts at {trip_start_of_day_at} and ends at {trip_end_of_day_at}.

Extra information about the user:
{user_extra_info}


---


Here are information that you have collected on the internet:
{internet_search_results_string}
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


def slot_in_schedule_loop(state: SlotInScheduleState, writer: StreamWriter):
    empty_slots = calculate_empty_slots(
        state.schedule_list, state.trip_start_of_day_at, state.trip_end_of_day_at
    )
    if not empty_slots:
        print("\n>>> Terminate slot_in_schedule_loop")
        return Command(
            goto="__end__",
        )

    print("\n>>> NODE: slot_in_schedule_loop")

    messages = state.slot_in_schedule_loop_messages
    should_add_system_prompt = False
    if len(messages) == 0:
        should_add_system_prompt = True
        messages.append(state.system_prompt)

    # Add system prompt for the first iteration

    human_message = HumanMessage(
        f"""
Fill the schedule with the best schedule items. Don't need to fill all at once because you'll be asked again until all slots are filled.

Current schedule:
{convert_schedule_items_to_string(state.schedule_list)}

Empty slots:
{empty_slots}

Important Rules:
- Fill in events in order, starting with the earliest empty time slot.
- Unless special circumstances, first check in the accommodation before starting the trip.
- Consider travel time between locations, and add the travel as an event.
- Prioritize the activities that are the most relevant to the user and don't overlap with the current schedule.
- Ensure meal times are accounted for and spaced appropriately throughout the day.
- Don't forget to come back to accommodation every night.
        """
    )

    messages.append(human_message)

    class Action(BaseModel):
        reasining_stage: str = Field(
            description="Before creating the schedule item, think out loud your reasoning behind this action."
        )
        schedule_item: ScheduleItem

    class SlotInScheduleResponse(BaseModel):
        actions: list[Action]

    response: list[SlotInScheduleResponse] = (
        ChatPromptTemplate.from_messages(messages)
        | chat_model.with_structured_output(SlotInScheduleResponse)
    ).invoke({})

    new_messages = []
    if should_add_system_prompt:
        new_messages.append(state.system_prompt)
    # Caveat! Don't need to add human message and AIMessage.
    # It's redundant as we provide it every iteration.

    return Command(
        goto=n(slot_in_schedule_loop),
        update={
            "slot_in_schedule_loop_messages": new_messages,
            "schedule_list": [action.schedule_item for action in response.actions],
        },
    )


g = StateGraph(OverallState)
g.add_edge(START, n(calculate_how_many_schedules))

g.add_node(n(calculate_how_many_schedules), calculate_how_many_schedules)
g.add_edge(n(calculate_how_many_schedules), n(add_fixed_schedules))
g.add_edge(n(calculate_how_many_schedules), n(add_terminal_schedules))

g.add_node(n(add_terminal_schedules), add_terminal_schedules)
g.add_edge(n(add_terminal_schedules), n(init_generate_queries_validation_loop))

g.add_node(n(add_fixed_schedules), add_fixed_schedules)
g.add_edge(n(add_fixed_schedules), n(init_generate_queries_validation_loop))

g.add_node(
    n(init_generate_queries_validation_loop), init_generate_queries_validation_loop
)
g.add_edge(n(init_generate_queries_validation_loop), n(generate_queries))

g.add_node(n(generate_queries), generate_queries)
g.add_edge(n(generate_queries), n(validate_and_improve_queries_loop))

g.add_node(n(validate_and_improve_queries_loop), validate_and_improve_queries_loop)

g.add_node(n(internet_search), internet_search)
g.add_edge(n(internet_search), n(init_slot_in_schedule_loop))

g.add_node(n(init_slot_in_schedule_loop), init_slot_in_schedule_loop)
g.add_edge(n(init_slot_in_schedule_loop), n(slot_in_schedule_loop))

g.add_node(n(slot_in_schedule_loop), slot_in_schedule_loop)
