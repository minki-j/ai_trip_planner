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
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
    RunnableParallel,
)
from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    RemoveMessage,
)

from app.state import (
    OverallState,
    InputState,
    ScheduleItem,
    ScheduleItemType,
    ScheduleItemTime,
    extend_list,
)
from app.models import Role
from app.llms import chat_model, perplexity_chat_model
from app.utils.utils import convert_schedule_items_to_string, calculate_empty_slots


MAX_NUM_OF_SCHEDULES = 100
MAX_NUM_OF_LOOPS = 100
HOURS_PER_QUERY = 6


def calculate_how_many_schedules(state: OverallState, writer: StreamWriter):
    return {n(state.trip_free_hours): 40}

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
        n(state.trip_free_hours): response.free_hours,
    }


def add_terminal_schedules(state: OverallState):
    print("\n>>> NODE: add_terminal_schedules")

    arrival_time = f"{state.trip_arrival_date} {state.trip_arrival_time}"
    departure_time = f"{state.trip_departure_date} {state.trip_departure_time}"

    return {
        n(state.schedule_list): [
            ScheduleItem(
                id=len(state.schedule_list) + 1,
                activity_type=ScheduleItemType.TERMINAL,
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
                id=len(state.schedule_list) + 2,
                activity_type=ScheduleItemType.TERMINAL,
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

    return {n(state.schedule_list): state.trip_fixed_schedules}


async def init_generate_search_query_loop(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: init_generate_search_query_loop")

    format_data = state.model_dump()
    format_data["trip_fixed_schedules_string"] = convert_schedule_items_to_string(
        state.trip_fixed_schedules, include_ids=False
    )

    system_prompt = SystemMessage(
        """
As an AI tour planner, you research travel options by performing internet searches to gather current information for a user.

The user will be visiting {trip_location}, staying at {trip_accommodation_location}, from {trip_arrival_date} {trip_arrival_time} to {trip_departure_date} {trip_departure_time}. They prefer a {trip_budget} trip with a focus on {trip_theme} and are particularly interested in {user_interests}. Their day starts at {trip_start_of_day_at} and ends at {trip_end_of_day_at}.

There are fixed schedules that the user has to follow:
{trip_fixed_schedules_string}

Extra information about the user:
{user_extra_info}


---


Here are examples of queries that you should generate. Each example is based on different trip scenario which are not included here. For the queries that you are going to generate, you should use the trip information provided above. 

1. 
Rationale: The user is visiting Quebec City and wants a Cultural & Heritage theme trip. I should look up if there is any museum related to indigenous culture in Quebec City.
Query: Museums related to indigenous culture in Quebec City

2.
Rationale: The user is visiting Cuba and wants a Relaxation & Wellness theme trip. I should look up which beach is the best to rest in Cuba.
Query: Best beaches in Cuba to relax

3.
Rationale: The user is visiting Iceland and wants a Adventure & Sports theme trip. I should look up which volcano is the most active in Iceland.
Query: Most active volcano in Iceland

4.
Rationale: It's important to have good food when you're visiting a new place. I should look up the best restaurants and cafes to eat at in Seoul.
Query: Best restaurants and cafes to eat at in Seoul

5.
Rationale: The user is visiting Qatar and wants a Entertainment & Party theme trip. I should look up which casino is the best to visit in Qatar.
Query: Best casinos in Qatar to visit


---


Important notes:
- You do not need to include the trip information in your queries. For instance, you do not need to specify the time that the user is visiting the location.
- You do not need to include queries for transportation between terminal and accommodation since it is already generated by other workflows.
    """.format(
            **format_data
        )
    )

    human_message = HumanMessage(
        f"""Read my trip information carefully, and generate upto {state.trip_free_hours // HOURS_PER_QUERY} queries to look up information on the internet. Make sure each query don't overlap with the other ones."""
    )

    class Queries(BaseModel):
        queries: list[Query]

    response: Queries = (
        ChatPromptTemplate.from_messages([system_prompt, human_message])
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
        "loop_iteration": 1,
        "search_queries": response_dict_with_id,
        "generate_search_query_loop_messages": [
            system_prompt,
            human_message,
            AIMessage(json.dumps(response_dict_with_id)),
        ],
    }


class Query(BaseModel):
    id: int = Field(default=None)
    rationale: str
    content: str


# For the loop of generating queries and validating them
# We need an temporary state that stores the message list and the queries
class GenerateSearchQueryLoopState(OverallState):
    loop_iteration: int
    search_queries: list[Query]
    generate_search_query_loop_messages: Annotated[list[AnyMessage], extend_list]


def generate_search_query_loop(
    state: GenerateSearchQueryLoopState, writer: StreamWriter
):
    print("\n>>> NODE: generate_search_query_loop")

    class GenerateSearchQueryActionsType(str, Enum):
        ADD = "add"
        REMOVE = "remove"
        MODIFY = "modify"
        SKIP = "skip"

    class GenerateSearchQueryActions(BaseModel):
        query_id: int
        rationale: str = Field(description="Explain why you want to do this action.")
        type: GenerateSearchQueryActionsType
        new_query_value: str = Field(description="Leave empty if type is remove")

    class GenerateSearchQueryLoopResponse(BaseModel):
        actions: list[GenerateSearchQueryActions] = Field(
            description="if is_current_queries_good_enough is True, leave this empty."
        )
        is_current_queries_good_enough: bool = Field(
            description="Return true if the current queries are good enough. Must return this field after actions field."
        )

    human_message = HumanMessage(
        "Review the queries for quality. Ensure they are diverse and not redundant. If any queries are redundant, keep only the best one. Add new queries relevant to my trip if any key aspects are missing. Modify queries that are too vague to make them more specific to my trip. For queries that meet the criteria, mark them with 'SKIP' as the action type. If all queries are good enough, return True for is_current_queries_good_enough."
    )

    response: GenerateSearchQueryLoopResponse = (
        ChatPromptTemplate.from_messages(
            [
                *state.generate_search_query_loop_messages,
                human_message,
            ]
        )
        | chat_model.with_structured_output(GenerateSearchQueryLoopResponse)
    ).invoke({})

    if (
        response.is_current_queries_good_enough
        or len(state.search_queries) >= state.trip_free_hours // HOURS_PER_QUERY
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
                for query in state.search_queries[:]
            ]
        )
    else:
        # Process actions to add, remove, and modify the queries
        queries = state.search_queries
        for action in response.actions:
            if action.activity_type == ActionsType.ADD:
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
            elif action.activity_type == ActionsType.REMOVE:
                # Remove query by ID
                queries[:] = [q for q in queries if q.id != action.query_id]
            elif action.activity_type == ActionsType.MODIFY:
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
                        f"- {action.rationale} / {action.activity_type.value} query with id {action.query_id} -> {action.new_query_value}"
                        for action in response.actions
                        if action.activity_type != ActionsType.SKIP
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
                n(state.loop_iteration): state.loop_iteration + 1,
                n(state.search_queries): queries,
                n(state.generate_search_query_loop_messages): [
                    human_message,
                    new_message,
                ],
            },
            goto=n(generate_search_query_loop),
        )


class InternetSearchState(InputState):
    query: str = Field(description="The query to search for.")


def internet_search(state: InternetSearchState, writer: StreamWriter):
    print("\n>>> NODE: internet_search")

    #! Excluded trip_theme, user_interests, and extra_info since they are distracting
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
- Do not use markdown format. Just use plain text.
- If possible (without making anything up), include practical tips for each tour recommendation, such as signature dishes to order, best photo spots, ways to get cheaper or easier tickets, best times to avoid crowds, portion sizes to expect, local customs or etiquette to be aware of, transportation tips, weather considerations, common scams or tourist traps to avoid, and unique souvenirs to look for.
    """.format(
        **state.model_dump()
    )

    response = (perplexity_chat_model | StrOutputParser()).invoke(prompt)

    # writer(
    #     {
    #         "title": f"{state.query}",
    #         "description": response,
    #     }
    # )

    result = {
        "query": state.query,
        "query_result": response,
    }

    return {"internet_search_result_list": [result]}


def init_fill_schedule_loop(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: init_fill_schedule_loop")

    format_data = state.model_dump()
    format_data["internet_search_results_string"] = "\n\n\n".join(
        [
            f"#{i+1}.\n\nSearch Query: {r['query']}\n\nResult:\n{r['query_result'].replace("---", "")}"
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


class FillScheduleLoopState(OverallState):
    system_prompt: SystemMessage
    fill_schedule_loop_messages: Annotated[list[AnyMessage], add_messages] = Field(
        default_factory=list
    )

class FillScheduleAction(BaseModel):
    reasoning: str = Field(
        description="Before creating the schedule item, think out loud your reasoning behind this action."
    )
    schedule_item: ScheduleItem


class FillScheduleResponse(BaseModel):
    actions: list[FillScheduleAction]


def fill_schedule_loop(state: FillScheduleLoopState, writer: StreamWriter):
    empty_slots = calculate_empty_slots(
        state.schedule_list, state.trip_start_of_day_at, state.trip_end_of_day_at
    )
    if not empty_slots:
        print("\n>>> Terminate: fill_schedule_loop")
        return Command(
            goto=n(validate_filled_schedule_loop),
        )

    print("\n>>> NODE: fill_schedule_loop")

    messages = state.fill_schedule_loop_messages
    should_add_system_prompt = False
    if len(messages) == 0:
        should_add_system_prompt = True
        messages.append(state.system_prompt)

    # Add system prompt for the first iteration

    human_message = HumanMessage(
        f"""
Fill the schedule with the best schedule items. Don't need to fill all at once because you'll be asked again until all slots are filled.

Current schedule:
{convert_schedule_items_to_string(state.schedule_list, include_ids=False)}

Empty slots:
{empty_slots}

Important Rules:
- Fill in events in order, starting with the earliest empty time slot.
- Consider travel time between locations, and add the travel as an event.
- Prioritize the activities that are the most relevant to the user and don't overlap with the current schedule.
- Ensure meal times are accounted for and spaced appropriately throughout the day.
- Don't forget to come back to accommodation every night.
- Leave 'id' field empty.
        """
    )

    messages.append(human_message)

    response: FillScheduleResponse = (
        ChatPromptTemplate.from_messages(messages)
        | chat_model.with_structured_output(FillScheduleResponse)
    ).invoke({})

    new_schedule_list = [
        action.schedule_item for action in response.actions
    ]
    # assign ids
    starting_id = len(state.schedule_list) + 1
    for i, item in enumerate(new_schedule_list):
        item.id = starting_id + i

    print(f"\n>>> New schedule list: {new_schedule_list}")

    new_messages = []
    if should_add_system_prompt:
        new_messages.append(state.system_prompt)
    # Caveat! Don't need to add human message and AIMessage.
    # It's redundant as we provide it every iteration.

    return Command(
        goto=n(fill_schedule_loop),
        update={
            n(state.fill_schedule_loop_messages): new_messages,
            n(state.schedule_list): new_schedule_list,
        },
    )


def fill_terminal_transportation_schedule(state: OverallState):
    print("\n>>> NODE: fill_terminal_transportation_schedule")

    prompt = """
You are an AI tour planner, and now finding transportation methods between the terminals and the accommodation.

Accommodation: {trip_accommodation_location} ({trip_location}).
Arrival: {trip_arrival_date} {trip_arrival_time}, {trip_arrival_terminal}.
Departure: {trip_departure_date} {trip_departure_time}, {trip_departure_terminal}.

You need to find the shortest path between the terminals and the accommodation.
Consider various methods such as public transportation, taxis/Uber, car rental, and walking.
Assume that the user has big luggage and needs to carry it all the way.
Pick the best 1-2 options and return them in detail with the following format:

Option #:
- Transportation type: ...
- Duration: ...
- Price: ...
- ETC.: ...
""".format(
        **state.model_dump()
    )

    second_prompt = """
Using the information above, create two TRANSPORT type schedule items: one for arrival and one for departure. 

- Make sure add details in description and suggestion fields. For location field, use 'A to B' format. A and B should be address of the place name. 
- Title should be 'Go to accommodation' and 'Go to terminal'. 
- For time field, use the following information: Arrival: {trip_arrival_date} {trip_arrival_time}, Departure: {trip_departure_date} {trip_departure_time}. 
- You should take the travel time into account and fill both start_time and end_time fields. For example, if the travel time is 1 hour, the start_time should be the arrival time, and the end_time should be the arrival time plus 1 hour. For departure, the start_time should be 1 hour before the terminal departure time.""".format(
        **state.model_dump()
    )

    response: FillScheduleResponse = (
        perplexity_chat_model
        | StrOutputParser()
        | RunnableLambda(lambda x: x + "\n\n---\n\n" + second_prompt)
        | chat_model.with_structured_output(FillScheduleResponse)
    ).invoke(prompt)

    # Adjust ids considering existing schedule items
    starting_id = len(state.schedule_list) + 1
    for i in range(len(response.actions)):
        response.actions[i].schedule_item.id = starting_id + i

    return {
        n(state.schedule_list): [action.schedule_item for action in response.actions],
    }


class ValidateScheduleResponse(BaseModel):
    reasoning: str = Field(
        description="Take time to thoroughly evaluate each schedule item against the criteria before start changing the schedule."
    )
    actions: list[ScheduleItem] = Field(
        description="Return an empty list if all the criteria are met. Otherwise, add actions to address issues with the schedule.\n\n- In order to remove an item, set its type to 'remove'.\n- In order to add an item, use any ScheduleItemType except 'remove'.\n- Modifications should be done by removing an existing item and adding a new one."
    )


def validate_filled_schedule_loop(state: OverallState):
    print("\n>>> NODE: validate_filled_schedule_loop")

    prompt = """
You are an AI tour planner, and just finished filling the schedule. Now you need to check if the schedule meets the following criteria:

- There should be at least 3 meals per day unless there is user-provided schedules during that period of time or it is arrival or departure day. (To recognize whether a schedule item is provided by user or not, see the id field. User-provided items start from 999)
- There should be proper transportation slots between locations.
- The user should start at accomodation and come back to the accomodation every day except arrival and departure day.
- There shouldn't be duplicated schedule items.


---


Here is the full schedule that you just filled:
{full_schedule_string}


---


If all the criteria are met, return an empty list.
    """.format(
        full_schedule_string=convert_schedule_items_to_string(state.schedule_list)
    )

    response: ValidateScheduleResponse = (
        chat_model.with_structured_output(ValidateScheduleResponse)
    ).invoke(prompt)

    if len(response.actions) == 0:
        print("\n>>> Terminate: validate_filled_schedule_loop")
        return Command(
            goto=END,
        )
    else:
        return Command(
            goto=n(validate_filled_schedule_loop),
            update={n(state.schedule_list): response.actions},
        )


g = StateGraph(OverallState)
g.add_edge(START, n(calculate_how_many_schedules))
g.add_edge(START, n(add_fixed_schedules))
g.add_edge(START, n(add_terminal_schedules))

g.add_node(calculate_how_many_schedules)
g.add_edge(n(calculate_how_many_schedules), "rendevous")

g.add_node(add_terminal_schedules)
g.add_edge(n(add_terminal_schedules), "rendevous")

g.add_node(add_fixed_schedules)
g.add_edge(n(add_fixed_schedules), "rendevous")

g.add_node("rendevous", RunnablePassthrough())
g.add_edge("rendevous", n(init_generate_search_query_loop))
g.add_edge("rendevous", n(fill_terminal_transportation_schedule))

g.add_node(init_generate_search_query_loop)
g.add_edge(n(init_generate_search_query_loop), n(generate_search_query_loop))

g.add_node(generate_search_query_loop)

g.add_node(internet_search)
g.add_edge(n(internet_search), n(init_fill_schedule_loop))

g.add_node(init_fill_schedule_loop)
g.add_edge(n(init_fill_schedule_loop), n(fill_schedule_loop))

g.add_node(fill_schedule_loop)

g.add_node(fill_terminal_transportation_schedule)

g.add_node(validate_filled_schedule_loop)
