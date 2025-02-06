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

from app.utils.convert_message_to_string import convert_messages_to_string


def is_introduction_done(state: OverallState, writer: StreamWriter):

    class IsIntroductionDone(BaseModel):
        rationale: str = Field(
            description="Think out loud why you think the introduction is done or not done."
        )
        is_done: bool = Field(description="True if the introduction is done.")
        reply: str = Field(
            description="If the introduction is done, transition to the next stage by asking where the user plans to travel. (Make it naturally fit to the current message history.) Otherwise, keep explaining or answering to the current message history."
        )

    response = (
        ChatPromptTemplate.from_template(
            """
You are an AI tour assistant helping {user_name} plan a trip to {trip_location} on {trip_date}. You're going to first talk to the user and get information about the trip. After that, you're going to gather tourist information on the internet and create a plan for the trip. The user will check the plan and can modify them by asking you. 

---

You are currently in the stage of introduction, explaining how this tour assistant works. Read the following message history and determine if the introduction is done. 

- If the introduction is done, reply with a transition to the next stage, keeping it naturally fit to the current message history. For example, "Okay, let's plan the trip now. Where do you plan to visit?"

- If the introduction is NOT done, keep explaining or answering to the current message history. 

---

This is the message history between you and the user:
{messages}
"""
        )
        | chat_model.with_structured_output(IsIntroductionDone)
    ).invoke(
        {
            "user_name": state.user_name,
            "trip_location": state.trip_location,
            "trip_date": state.trip_date,
            "messages": convert_messages_to_string(state.messages),
        }
    )

    if response.is_done:
        writer(
            {
                "role": Role.ReasoningStep.value,
                "message": "Introduction stage is done.",
            }
        )
        return Command(
            update={"messages": [AIMessage(response.reply)]},
            goto="__end__",
        )
    else:
        print("intro not done. reply: ", response.reply)
        return Command(
            update={
                "intro_rationale": response.rationale,
                "intro_reply": response.reply,
            },
            goto=n(verify_reply),
        )


def verify_reply(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: generate_paraphrase")

    #     response = (
    #         ChatPromptTemplate.from_template(
    #             """
    # You are an AI tour assistant helping {user_name} plan a trip to {trip_location} on {trip_date}.

    # Here is how this tour assistant works: You  first talk to {user_name} and get information about the trip. After that, you gather tourist information on the internet and create a plan for the trip. {user_name} will check the plan and can modify them by asking you.

    # ---

    # Message history:
    # {messages}

    # ---

    # Now, verify if this reply fits with the introduction

    # reply: {reply}

    # """
    #         )
    #         | chat_model
    #     ).invoke(
    #         {
    #             "user_name": state.user_name,
    #             "trip_location": state.trip_location,
    #             "trip_date": state.trip_date,
    #             "reply": state.intro_reply,
    #             "messages": convert_messages_to_string(state.messages),
    #         }
    #     )

    print("State", state)
    # print("state.intro_reply: ", state.intro_reply)

    writer(
        {
            "role": Role.ReasoningStep.value,
            "message": "verified reply",
        }
    )

    return {
        "messages": [AIMessage(state.intro_reply)],
    }


g = StateGraph(OverallState)
g.add_edge(START, n(is_introduction_done))

g.add_node(n(is_introduction_done), is_introduction_done)

g.add_node(n(verify_reply), verify_reply)
