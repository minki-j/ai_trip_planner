import asyncio
from varname import nameof as n

from langgraph.graph import START, END, StateGraph

from app.state import OverallState, Stage

from .generate_schedule_graph import g as generate_schedule
from app.utils.compile_graph import compile_graph_with_async_checkpointer

async def init_generate_schedule():
    global generate_schedule
    generate_schedule = await compile_graph_with_async_checkpointer(
        generate_schedule, "generate_schedule"
    )
asyncio.run(init_generate_schedule())

def stage_router(state: OverallState):
    print("\n>>> NODE: stage_router")

    if state.current_stage == Stage.END:
        return END
    elif state.current_stage == Stage.FIRST_GENERATION:
        return n(generate_schedule)
    # TODO: Implement modify stage
    # elif state.current_stage == Stage.MODIFY:
    #     return n(generate_schedule) 
    else:
        raise ValueError(f"Invalid stage: {state.current_stage}")

g = StateGraph(OverallState)
g.add_conditional_edges(
    START,
    stage_router,
    [n(generate_schedule), END],
)

g.add_node(n(generate_schedule), generate_schedule)
