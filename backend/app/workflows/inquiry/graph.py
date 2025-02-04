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


async def introduction_graph(state: OverallState, writer: StreamWriter):
    print("\n>>> NODE: generate_paraphrase")

    response = await (
        ChatPromptTemplate.from_template(
            """
Prompt in here
"""
        )
        | chat_model
    ).ainvoke(
        {
            "input": state.input,
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
g.add_edge(START, n(introduction_graph))

g.add_node(n(introduction_graph), introduction_graph)
g.add_edge(n(introduction_graph), END)
