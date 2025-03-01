import json
from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field, create_model
from typing import Annotated

from langgraph.graph import START, END, StateGraph, add_messages
from langgraph.types import StreamWriter, Command, Send

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
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
from app.llms import (
    chat_model_anthropic_first,
    chat_model_openai_first,
    perplexity_chat_model,
    reasoning_model,
    small_model_anthropic_first,
)
from app.utils.utils import (
    convert_schedule_items_to_string,
    calculate_empty_slots,
    calculate_trip_free_hours,
    determine_model
)

from notdiamond import init_NotDiamond_client
nd_client = init_NotDiamond_client(router_only=True)

FREE_HOURS_PER_QUERY = 6
MAX_INTERNET_SEARCH = 10


class ScheduleAction(BaseModel):
    reasoning: str = Field(
        description="Before generating the schedule item, think out loud your reasoning behind this action."
    )
    schedule_item: ScheduleItem = Field(
        description="The schedule item to be added to the schedule. Set ID to 0."
    )


class FillScheduleResponse(BaseModel):
    actions: list[ScheduleAction]


def calculate_trip_free_hours_node(state: OverallState, writer: StreamWriter):

    free_hours: int = calculate_trip_free_hours(
        state.trip_arrival_date,
        state.trip_arrival_time,
        state.trip_departure_date,
        state.trip_departure_time,
        state.trip_start_of_day_at,
        state.trip_end_of_day_at,
        state.trip_fixed_schedules,
    )

    writer({"short": f"Calculated free hours: {free_hours}", "long": None})

    return {
        n(state.trip_free_hours): free_hours,
    }


def add_fixed_schedules(state: OverallState, writer: StreamWriter):
    if not state.trip_fixed_schedules:
        return {}

    writer({"short": "Adding fixed schedules", "long": None})

    # check all fixed schedules are type of ScheduleItem
    if not all(isinstance(s, ScheduleItem) for s in state.trip_fixed_schedules):
        raise ValueError(
            "Invalid fixed schedules provided. They must be a list of ScheduleItem."
        )

    return {n(state.schedule_list): state.trip_fixed_schedules}


def add_terminal_schedules(state: OverallState, writer: StreamWriter):
    writer({"short": "Adding terminal schedules", "long": None})

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


def fill_terminal_transportation_schedule(state: OverallState, writer: StreamWriter):
    writer({"short": "Adding terminal <-> accommodation schedules", "long": None})

    prompt_for_perplexity = """
You are an AI tour planner, and now finding transportation methods between the terminals and the accommodation.

Accommodation: {trip_accommodation_location} ({trip_location}).
Arrival: {trip_arrival_date} {trip_arrival_time}, {trip_arrival_terminal}.
Departure: {trip_departure_date} {trip_departure_time}, {trip_departure_terminal}.

You need to find the shortest path between the terminals and the accommodation.
Consider various methods such as public transportation, taxis/Uber, car rental, and walking.
Assume that the user has big luggage and needs to carry it all the way.
Pick the best 1-2 options and return them in detail with the following format:

1.  From the terminal to the accommodation:
Option #:
- Transportation type: ...
- Duration: ...
- Price: ...
...

2. From the accommodation to the terminal:
Option #:
- Transportation type: ...
- Duration: ...
- Price: ...
...

""".format(
        **state.model_dump()
    ).strip()

    prompt_for_chat_model = """
Using the information above, create two TRANSPORT type schedule items: one for arrival and one for departure. 

- Make sure add details in description and suggestion fields. For location field, use 'A to B' format. A and B should be address of the place name. 
- Title should be 'Go to accommodation' and 'Go to terminal'. 
- For time field, use the following information: Arrival: {trip_arrival_date} {trip_arrival_time}, Departure: {trip_departure_date} {trip_departure_time}. 
- You should take the travel time into account and fill both start_time and end_time fields. For example, if the travel time is 1 hour, the start_time should be the arrival time, and the end_time should be the arrival time plus 1 hour. For departure, the start_time should be 1 hour before the terminal departure time.
- If possible include cost in the suggestion field.
""".format(
        **state.model_dump()
    ).strip()

    perplexity_response: str = (
        perplexity_chat_model
        | StrOutputParser()
    ).invoke(prompt_for_perplexity)

    model = determine_model(nd_client, [HumanMessage(content=perplexity_response + "\n\n---\n\n" + prompt_for_chat_model)])
    response: FillScheduleResponse = model.with_structured_output(FillScheduleResponse).invoke(perplexity_response + "\n\n---\n\n" + prompt_for_chat_model)

    # Adjust ids considering existing schedule items
    starting_id = len(state.schedule_list) + 1
    for i in range(len(response.actions)):
        response.actions[i].schedule_item.id = starting_id + i

    return {
        n(state.schedule_list): [action.schedule_item for action in response.actions],
    }


class QueryWithRationale(BaseModel):
    id: int = Field(default=None)
    rationale: str
    query: str


async def init_generate_search_query_loop(state: OverallState, writer: StreamWriter):
    writer({"short": "Generating queries for internet search", "long": None})

    format_data = state.model_dump()
    format_data["trip_fixed_schedules_string"] = convert_schedule_items_to_string(
        state.trip_fixed_schedules,
        include_ids=False,
        include_description=True,
        include_suggestion=False,
    )

    system_prompt = SystemMessage(
        """
As an AI tour planner, you conduct internet research to gather the travel options tailored to the user's preferences and trip information.

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
- You do not need to generate queries for transportation between terminal and accommodation since it is already generated by other workflows.
    """.format(
            **format_data
        ).strip()
    )

    human_message = HumanMessage(
        f"""Read my trip information carefully, and generate upto {state.trip_free_hours // FREE_HOURS_PER_QUERY} queries to look up information on the internet. Make sure each query don't overlap with the other ones.""".strip()
    )

    class Queries(BaseModel):
        queries: list[QueryWithRationale]

    model = determine_model(nd_client, [system_prompt, human_message])

    response: Queries = (
        ChatPromptTemplate.from_messages([system_prompt, human_message])
        | model.with_structured_output(Queries)
    ).invoke({})

    writer(
        {
            "short": f"Generated {len(response.queries)} queries",
            "long": {
                "title": "Queries to look up on the internet",
                "description": "\n".join([f"- {q.query}" for q in response.queries]),
            },
        }
    )

    response_dict_with_id = []
    for i, query in enumerate(response.queries):
        query_dict = query.model_dump()
        query_dict["id"] = i
        response_dict_with_id.append(query_dict)

    return {
        "loop_iteration": 1,
        "search_queries": response_dict_with_id,
        "generate_search_query_loop_messages": [
            system_prompt,
            human_message,
            AIMessage(json.dumps(response_dict_with_id)),
        ],
    }


# For the loop of generating queries and validating them
# We need an temporary state that stores the message list and the queries
class GenerateSearchQueryLoopState(OverallState):  # Inherit from OverallState
    loop_iteration: int
    search_queries: list[QueryWithRationale]
    generate_search_query_loop_messages: Annotated[list[AnyMessage], extend_list]


def generate_search_query_loop(
    state: GenerateSearchQueryLoopState, writer: StreamWriter
):
    writer({"short": "Reviewing search queries for improvement (loop)", "long": None})

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

    model = determine_model(nd_client, [
                *state.generate_search_query_loop_messages,
                human_message,
            ])

    response: GenerateSearchQueryLoopResponse = (
        ChatPromptTemplate.from_messages(
            [
                *state.generate_search_query_loop_messages,
                human_message,
            ]
        )
        | model.with_structured_output(
            GenerateSearchQueryLoopResponse
        )
    ).invoke({})

    if (
        response.is_current_queries_good_enough
        or len(state.search_queries) >= state.trip_free_hours // FREE_HOURS_PER_QUERY
    ):
        # If the current queries are good enough or the maximum number of queries has been reached, then terminate the loop and start the internet search nodes in parallel
        writer(
            {
                "short": f"Starting {len(state.search_queries)} internet search in parallel",
                "long": None,
            }
        )

        # Call the internet_search node for each query in parallel
        return Command(
            goto=[
                Send(
                    n(internet_search),
                    InternetSearchState.model_validate(
                        {
                            **state.model_dump(),
                            "query": query.query,
                        }
                    ),
                )
                for query in state.search_queries[:MAX_INTERNET_SEARCH]
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
                new_query = QueryWithRationale(
                    id=next_id,
                    rationale=action.rationale,
                    query=action.new_query_value,
                )
                queries.append(new_query)
            elif action.activity_type == ActionsType.REMOVE:
                # Remove query by ID
                queries[:] = [q for q in queries if q.id != action.query_id]
            elif action.activity_type == ActionsType.MODIFY:
                # Modify existing query by ID
                for query in queries:
                    if query.id == action.query_id:
                        query.query = action.new_query_value
                        break

        writer({"short": f"Found {len(response.actions)} improvements", "long": None})

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


class InternetSearchState(InputState):  # Inherit from InputState
    query: str = Field(description="The query to search for.")


def internet_search(state: InternetSearchState, writer: StreamWriter):

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
- If possible (without making anything up), include practical tips for each tour recommendation, such as signature dishes to order, best photo spots, ways to get cheaper or easier tickets, best times to avoid crowds, portion sizes to expect, local customs or etiquette to be aware of, transportation tips, weather considerations, common scams or tourist traps to avoid, and unique souvenirs to look for.
- Do NOT include citations.
- Do NOT use Markdown format. Just use plain text with bullet points and numbered lists. 
    """.format(
        **state.model_dump()
    ).strip()

    response = (perplexity_chat_model | StrOutputParser()).invoke(prompt)

    model = determine_model(nd_client, [HumanMessage(f"Summarize the following internet search result in a single paragraph. If there are list of tourist attractions, places of interest, or landmarks, include all of them in the summary. Here is the result:\n{response}")])

    summarized_response = model.invoke(
        f"Summarize the following internet search result in a single paragraph. If there are list of tourist attractions, places of interest, or landmarks, include all of them in the summary. Here is the result:\n{response}"
    )

    writer(
        {
            "short": None,
            "long": {
                "title": f"Internet search result",
                "description": f"**Query**: {state.query}\n\n**Summarized result**: {summarized_response.content}",
            },
        }
    )

    result = {
        "query": state.query,
        "query_result": response,
    }

    return {"internet_search_result_list": [result]}


def init_fill_schedule_loop(state: OverallState, writer: StreamWriter):

    format_data = state.model_dump()
    format_data["internet_search_results_string"] = "\n\n\n".join(
        [
            f"# {i+1}.\n\nSearch Query: {r['query']}\n\nResult:\n{r['query_result'].replace("---", "")}"
            for i, r in enumerate(state.internet_search_result_list)
        ]
    )

    system_prompt = SystemMessage(
        """
<warning>DO NOT RETURN AN EMPTY RESPONSE!! YOU HAVE ENOUGH OUTPUT TOKENS</warning>

As an AI tour planner, you help arrange travel schedules for users' trips based on the information you have collected from the internet.

The user will be visiting {trip_location}, staying at {trip_accommodation_location}, from {trip_arrival_date} {trip_arrival_time} to {trip_departure_date} {trip_departure_time}. They prefer a {trip_budget} trip with a focus on {trip_theme} and are particularly interested in {user_interests}. Their day starts at {trip_start_of_day_at} and ends at {trip_end_of_day_at}.

Extra information about the user:
{user_extra_info}


---


Here are information that you have collected on the internet:

{internet_search_results_string}


---


<warning>DO NOT RETURN AN EMPTY RESPONSE!! YOU HAVE ENOUGH OUTPUT TOKENS</warning>
    """.format(
            **format_data
        ).strip()
    )

    return {
        "fill_schedule_loop_messages": [system_prompt],
    }


FILL_SCHEDULE_CRITERIA_LIST = [
    """Fill in events in order, starting with the earliest empty time slot.""",
    """Consider travel time between locations, and add the travel as an event using 'transportation' or 'walk' type.""",
    """Prioritize the activities that are the most relevant to the user and don't overlap with the current schedule.""",
    """Include as detail as possible the information of the activities in 'description' and 'suggestion' field.""",
    """Ensure meal times(breakfast, lunch, dinner, snack) are accounted for and spaced appropriately throughout the day.""",
    """Don't forget to come back to accommodation at the end of the day.""",
    """Make sure to have enough time to arrive to the departure terminal. No big events right before the departure.""",
]


class FillScheduleLoopState(OverallState):  # Inherit from OverallState
    fill_schedule_loop_messages: Annotated[list[AnyMessage], add_messages] = Field(
        default_factory=list
    )


def fill_schedule_loop(state: FillScheduleLoopState, writer: StreamWriter):
    empty_slots = calculate_empty_slots(
        state.schedule_list, state.trip_start_of_day_at, state.trip_end_of_day_at
    )
    if not empty_slots:
        writer({"short": "Completed filling all schedule items", "long": None})
        return Command(
            goto=n(validate_full_schedule_loop),
        )

    writer({"short": "Filling schedule items (loop)", "long": None})

    messages = state.fill_schedule_loop_messages

    #! Added an ad hoc warning message since Claude sonnet 3.5 keeps returning an empty response half of the time.
    #! Make sure to remove this after the model gets better.
    human_message = HumanMessage(
        f"""
<warning>DO NOT RETURN AN EMPTY RESPONSE!! YOU HAVE ENOUGH OUTPUT TOKENS</warning>

Fill the schedule with the best schedule items. Don't need to fill all at once because you'll be asked again until all slots are filled.

Current schedule:
{convert_schedule_items_to_string(state.schedule_list, include_ids=False, include_description=False, include_suggestion=False)}

Empty slots:
{empty_slots}

Important Rules:
{"\n".join([f"- {c}" for c in FILL_SCHEDULE_CRITERIA_LIST])}


<warning>DO NOT RETURN AN EMPTY RESPONSE!! YOU HAVE ENOUGH OUTPUT TOKENS</warning>
""".strip()
    )

    messages.append(human_message)

    model = determine_model(nd_client, messages)

    response: FillScheduleResponse = (
        ChatPromptTemplate.from_messages(messages)
        | model.with_structured_output(FillScheduleResponse)
    ).invoke({})

    # Note: This creates a new list but the items inside are references to the original objects
    new_schedule_list = [action.schedule_item for action in response.actions]

    starting_id = len(state.schedule_list) + 1

    # Since we're working with references, this updates both new_schedule_list
    # and the original items in response.actions simultaneously
    for i, item in enumerate(new_schedule_list):
        item.id = starting_id + i

    new_messages = []
    new_messages.extend(
        [
            human_message,
            AIMessage(
                convert_schedule_items_to_string(
                    [action.schedule_item for action in response.actions],
                    include_ids=True,
                    include_description=True,
                    include_suggestion=True,
                )
            ),
        ]
    )
    writer(
        {
            "short": f"Added {len(response.actions)} schedule items",
            "long": {
                "title": f"Added {len(response.actions)} schedule items",
                "description": convert_schedule_items_to_string(
                    [action.schedule_item for action in response.actions],
                    include_ids=False,
                    include_description=False,
                    include_suggestion=False,
                    include_heading=False,
                ),
            },
        }
    )

    return Command(
        goto=n(fill_schedule_reflection),
        update={
            n(state.fill_schedule_loop_messages): new_messages,
            n(state.schedule_list): new_schedule_list,
        },
    )


def fill_schedule_reflection(state: FillScheduleLoopState, writer: StreamWriter):
    writer({"short": "Reflecting on added schedule items", "long": None})

    criteria_instruction = (
        "Think out loud if provided schedule items meet the following criteria:"
    )
    fill_schedule_criteria_list = [
        criteria_instruction + c for c in FILL_SCHEDULE_CRITERIA_LIST
    ]

    # Dynamically create field definitions for the FillScheduleReflectionResponse class
    fields = {
        f"reasoning_for_criteria_{i+1}": (str, Field(description=criterion))
        for i, criterion in enumerate(fill_schedule_criteria_list)
    }

    # Add the actions field
    fields["actions"] = (
        list[ScheduleAction],
        Field(
            description="""
Return an empty list if all the criteria are met. Otherwise, add actions to address issues with the schedule.

1. To REMOVE an item: set its type to 'remove'.
2. To MODIFY an item: return the new item with the same ID as the original item with any ScheduleItemType other than 'remove'.
3. To ADD a new item: use any ScheduleItemType except 'remove' with a new ID. (Be careful with IDs -- You need to provide an ID that doesn't match any existing item. If you do, the item will be modified instead.)

Important!! This field is required. Don't forget to return an empty list if all the criteria are met!
            """.strip()
        ),
    )

    # Create the FillScheduleReflectionResponse class dynamically
    FillScheduleReflectionResponse = create_model(
        "FillScheduleReflectionResponse", **fields, __base__=BaseModel
    )

    messages = [
        *state.fill_schedule_loop_messages,  # messages in the fill_schedule_loop
        HumanMessage(
            "Verify if the schedule items you just returned meet the provided criteria. Focus only on the items within your current scope, not the entire schedule. For example, if you returned schedules from March 9th 3:00 PM to March 9th 5:00 PM, you only need to evaluate that timeframe."
        ),
    ]  # did not include the system prompt

    model = determine_model(nd_client, messages)

    # Using O3-mini
    response = (
        ChatPromptTemplate.from_messages(messages)
        | model.with_structured_output(FillScheduleReflectionResponse)
    ).invoke({})

    if len(response.actions) > 0:
        writer(
            {
                "short": f"Found {len(response.actions)} improvements",
                "long": {
                    "title": f"Found {len(response.actions)} improvements in added schedule items",
                    "description": convert_schedule_items_to_string(
                        [action.schedule_item for action in response.actions],
                        include_ids=False,
                        include_description=False,
                        include_suggestion=False,
                        include_heading=False,
                    ),
                },
            }
        )
    else:
        writer({"short": "All added schedule items have been verified", "long": None})

    messages_to_remove = [
        RemoveMessage(msg.id) for msg in state.fill_schedule_loop_messages[-2:]
    ]  # We need to remove these messages because we are going to summarize them in the prompt of the next loop

    return Command(
        goto=n(fill_schedule_loop),
        update={
            n(state.schedule_list): [
                action.schedule_item for action in response.actions
            ],
            n(state.fill_schedule_loop_messages): messages_to_remove,
        },
    )


def validate_full_schedule_loop(state: OverallState, writer: StreamWriter):
    writer({"short": "Reviewing full schedule", "long": None})

    validate_filled_schedule_criteria_list = [
        """
There should be at least 3 meals per day unless 
1. The user-provided schedules overlap with the meal time.
2. It is arrival or departure day, and the meal time is before or after the terminal schedule
        """.strip(),
        """
There should be proper transportation slots between locations.
Here are some examples:

Ex 1.
Schedule:
- 6 | 2025-02-19 13:30 ~ 14:00 | other | Check-in at Accommodation | 891 Amsterdam Avenue 
- 9 | 2025-02-19 14:00 ~ 14:30 | historical_site | Visit Grand Central Terminal | 89 E 42nd St, New York, NY 10017

Response: It doesn't meet the criteria, because it didn't account for the travel time from 891 Amsterdam Avenue to 89 E 42nd St, whic takes about 30 minutes. I need to modify the 

        """.strip(),
        """
The user should start at accomodation and come back to the accomodation every day except arrival and departure day.
        """.strip(),
        """
There shouldn't be duplicated schedule items.
        """.strip(),
    ]
    criteria_instruction = (
        "Think out loud if provided schedule meets the following criteria:"
    )
    validate_filled_schedule_criteria_list = [
        criteria_instruction + c for c in validate_filled_schedule_criteria_list
    ]

    # Dynamically create field definitions for the ValidateScheduleResponse class
    fields = {
        f"reasoning_for_criteria_{i+1}": (str, Field(description=criterion))
        for i, criterion in enumerate(validate_filled_schedule_criteria_list)
    }

    # Add the actions field
    fields["actions"] = (
        list[ScheduleAction],
        Field(
            description="""
Return an empty list if all the criteria are met. Otherwise, add actions to address issues with the schedule.

1. To REMOVE an item: set its type to 'remove'.
2. To MODIFY an item: return the new item with the same ID as the original item with any ScheduleItemType other than 'remove'.
3. To ADD a new item: use any ScheduleItemType except 'remove' with a new ID. (Be careful with IDs -- You need to provide an ID that doesn't match any existing item. If you do, the item will be modified instead.)
            """.strip()
        ),
    )

    # Create the ValidateScheduleResponse class dynamically
    ValidateScheduleResponse = create_model(
        "ValidateScheduleResponse", **fields, __base__=BaseModel
    )

    prompt = """
You are an AI tour planner, and just finished filling the schedule. Now you need to check if the schedule meets the provided criteria.


---


Here is the full schedule that you just filled:
{full_schedule_string}
    """.format(
        full_schedule_string=convert_schedule_items_to_string(
            state.schedule_list,
            include_ids=True,
            include_description=True,
            include_suggestion=True,
        ),
    ).strip()

    model = determine_model(nd_client, [HumanMessage(prompt)])

    # Using O3-mini
    response = (
        model.with_structured_output(ValidateScheduleResponse)
    ).invoke(prompt)

    if len(response.actions) == 0:
        print("\n>>> Workflow completed!")
        return Command(
            goto=END,
        )
    else:
        writer(
            {
                "short": f"Found {len(response.actions)} improvements",
                "long": {
                    "title": f"Found {len(response.actions)} improvements in final schedule",
                    "description": convert_schedule_items_to_string(
                        [action.schedule_item for action in response.actions],
                        include_ids=False,
                        include_description=False,
                        include_suggestion=False,
                        include_heading=False,
                    ),
                },
            }
        )

        return Command(
            goto=n(validate_full_schedule_loop),
            update={
                n(state.schedule_list): [
                    action.schedule_item for action in response.actions
                ]
            },
        )


g = StateGraph(OverallState)
g.add_edge(START, n(calculate_trip_free_hours_node))
g.add_edge(START, n(add_fixed_schedules))
g.add_edge(START, n(add_terminal_schedules))

g.add_node(calculate_trip_free_hours_node)
g.add_edge(n(calculate_trip_free_hours_node), "rendevous")

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

g.add_node(fill_schedule_reflection)

g.add_node(fill_terminal_transportation_schedule)

g.add_node(validate_full_schedule_loop)
