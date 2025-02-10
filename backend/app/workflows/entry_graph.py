import asyncio
from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field

from langgraph.graph import START, END, StateGraph
from langgraph.types import StreamWriter, Command

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

from app.state import OverallState
from app.llm import chat_model

from app.models import Stage

from .generate.graph import g as generate_schedule
from app.utils.compile_graph import compile_graph_with_async_checkpointer

async def init_generate_schedule():
    global generate_schedule
    generate_schedule = await compile_graph_with_async_checkpointer(
        generate_schedule, "generate_schedule"
    )
asyncio.run(init_generate_schedule())

def stage_router(state: OverallState):
    print("\n>>> NODE: stage_router")

    if state.stage == Stage.FIRST_GENERATION:
        return n(generate_schedule)
    elif state.stage == Stage.MODIFY:
        return n(generate_schedule) #! Not implemented yet
    else:
        raise ValueError(f"Invalid stage: {state.stage}")

g = StateGraph(OverallState)
g.add_conditional_edges(
    START,
    stage_router,
    [n(generate_schedule)],
)

g.add_node(n(generate_schedule), generate_schedule)