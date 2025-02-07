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

from .generate_plan.graph import g as generate_plan
from app.utils.compile_graph import compile_graph_with_sync_checkpointer

generate_plan = compile_graph_with_sync_checkpointer(generate_plan, "assist")


def stage_router(state: OverallState):
    print("\n>>> NODE: stage_router")

    if state.stage == Stage.FIRST_GENERATION:
        return n(generate_plan)
    elif state.stage == Stage.APPLY_UPDATED_TRIP_INFO:
        return n(generate_plan) #! 
    elif state.stage == Stage.MODIFY:
        return n(generate_plan) #!
    else:
        raise ValueError(f"Invalid stage: {state.stage}")


g = StateGraph(OverallState, input=InputState, output=OutputState)
g.add_conditional_edges(
    START,
    stage_router,
    [n(generate_plan)],
)


g.add_node(n(generate_plan), generate_plan)
g.add_edge(n(generate_plan), END)
