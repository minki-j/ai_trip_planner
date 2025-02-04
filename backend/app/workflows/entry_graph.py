from varname import nameof as n
from enum import Enum
from pydantic import BaseModel, Field

from langgraph.graph import START, END, StateGraph
from langgraph.types import StreamWriter, Command

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.state import OverallState, InputState, OutputState
from app.llm import chat_model


async def generate_paraphrase(state: OverallState):
    print("\n>>> NODE: generate_paraphrase")

    response = await (
        ChatPromptTemplate.from_template(
            """
Paraphrase the following text for ESL student to understand it better.
- Use simpler vocabulary.
- Change idiomatic expressions in a clear way.
- Use more simple sentence structure.
- The student's English level: {englishLevel}

---

text: {input}

---

Don't include "here is the paraphrased text: " or "Sure, let's paraphrase the text". Just return the paraphrased text.
"""
        )
        | chat_model
    ).ainvoke(
        {
            "input": state.input,
            "englishLevel": state.englishLevel,
        }
    )

    return {
        "paraphrase": response,
    }


g = StateGraph(OverallState, input=InputState, output=OutputState)
g.add_edge(START, n(generate_paraphrase))

g.add_node(n(generate_paraphrase), generate_paraphrase)
g.add_edge(n(generate_paraphrase), n(generate_breakdown))

g.add_node(n(generate_breakdown), generate_breakdown)
g.add_edge(n(generate_breakdown), END)
