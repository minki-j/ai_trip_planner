from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field

from langgraph.graph import START, END, StateGraph
from langgraph.types import StreamWriter, Command

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from app.state import OverallState, InputState, OutputState
from app.llm import chat_model

from app.models import Role

from ...utils.convert_message_to_string import convert_messages_to_string


async def inquire(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: generate_paraphrase")

    class Info(Enum):
        TRIP_TRANSPORTATION_SCHEDULE = "trip_transportation_schedule"
        TRIP_LOCATION = "trip_location"
        TRIP_DURATION = "trip_duration"
        TRIP_BUDGET = "trip_budget"
        TRIP_THEME = "trip_theme"
        TRIP_FIXED_SCHEDULES = "trip_fixed_schedules"
        USER_INTERESTS = "user_interests"
        USER_EXTRA_INFO = "user_extra_info"

    class InquireResponse(BaseModel):
        missing_info: Info = Field(description="The information that is missing from the user's input.")
        next_message: str = Field(description="The next message to send to the user inquiring about the missing information.")

    response = await (
        ChatPromptTemplate.from_template(
            """
You are an tour assistant helping users to plan their trip. At the momenet, you are asking the user about their trip. You need to fill the missing information. 

---

## Trip information:
trip_transportation_schedule: {trip_transportation_schedule}
trip_location: {trip_location}
trip_duration: {trip_duration}
trip_budget: {trip_budget}
trip_theme: {trip_theme}
trip_fixed_schedules: {trip_fixed_schedules}
user_interests: {user_interests}
user_extra_info: {user_extra_info}

---

## This is the current conversation with you and the user:
{messages}

---

Pick one 
"""
        )
        | chat_model.with_structured_output(InquireResponse)
    ).ainvoke(
        {
            "trip_transportation_schedule": state.trip_transportation_schedule,
            "trip_location": state.trip_location,
            "trip_duration": state.trip_duration,
            "trip_budget": state.trip_budget,
            "trip_theme": state.trip_theme,
            "trip_fixed_schedules": state.trip_fixed_schedules,
            "user_interests": state.user_interests,
            "user_extra_info": state.user_extra_info,
            "messages": convert_messages_to_string(state.messages),
        }
    )

    writer(
        {
            "role": Role.ReasoningStep.value,
            "message": "streamed reply",
        }
    )

    return {
        "messages": [response],
    }


g = StateGraph(OverallState, input=InputState, output=OutputState)
g.add_edge(START, n(inquire))

g.add_node(n(inquire), inquire)
g.add_edge(n(inquire), END)
