import os

from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from pymongo import AsyncMongoClient

async def compile_graph_with_async_checkpointer(graph, graph_name):
    mongodb_client = AsyncMongoClient(os.getenv("MONGODB_URI_LANGGRAPH_CHECKPOINTER"))
    checkpointer = AsyncMongoDBSaver(mongodb_client)

    graph = graph.compile(checkpointer=checkpointer)

    with open(f"./app/workflow_diagrams/{graph_name}.png", "wb") as f:
        f.write(graph.get_graph(xray=1).draw_mermaid_png())

    return graph
