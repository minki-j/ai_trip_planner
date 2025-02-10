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

The user will be visiting {trip_location} (staying at {trip_accomodation_location}). The user wants the trip to be {trip_budget}.

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

---

Now, collect information about the following query: 
{query}


---

## Important Rules
- Keep in mind the user's trip information, and sort the results in a way that the most relevant information is at the top.
- You don't need to plan the full schedule, just collect information about the query.
- Make sure only include information that is available from {trip_arrival_date} {trip_arrival_time} to {trip_departure_date} {trip_departure_time}.
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
