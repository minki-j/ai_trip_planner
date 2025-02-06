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

from app.models import Stage, Role

from .introduction.graph import g as introduction_graph
from .inquiry.graph import g as inquiry_graph
from .assist.graph import g as assist_graph
from app.utils.compile_graph import compile_graph_with_sync_checkpointer

introduction_graph = compile_graph_with_sync_checkpointer(
    introduction_graph, "introduction"
)
inquiry_graph = compile_graph_with_sync_checkpointer(inquiry_graph, "inquiry")
assist_graph = compile_graph_with_sync_checkpointer(assist_graph, "assist")


def add_user_message(state: OverallState):
    print("\n>>> NODE: add_user_message")
    messages = []

    if len(state.messages) == 0:
        messages.append(
            AIMessage(
                "Hi, I'm your tour assistant! May I introduce how this tour assistant works?"
            )
        )

    messages.append(HumanMessage(state.input))

    return {
        "messages": messages,
    }


def stage_router(state: OverallState):
    print("\n>>> NODE: stage_router")

    if state.stage == Stage.INTRODUCTION:
        return n(introduction_graph)
    elif state.stage == Stage.INQUIRY:
        return n(inquiry_graph)
    elif state.stage == Stage.ASSIST:
        return n(assist_graph)
    else:
        raise ValueError(f"Invalid stage: {state.stage}")


g = StateGraph(OverallState, input=InputState, output=OutputState)
g.add_edge(START, n(add_user_message))

g.add_node(n(add_user_message), add_user_message)
g.add_conditional_edges(
    n(add_user_message),
    stage_router,
    [n(introduction_graph), n(inquiry_graph), n(assist_graph)],
)


g.add_node(n(introduction_graph), introduction_graph)
g.add_edge(n(introduction_graph), END)

g.add_node(n(inquiry_graph), inquiry_graph)
g.add_edge(n(inquiry_graph), END)

g.add_node(n(assist_graph), assist_graph)
g.add_edge(n(assist_graph), END)
