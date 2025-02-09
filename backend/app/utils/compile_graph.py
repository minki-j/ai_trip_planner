import os
from pymongo import AsyncMongoClient
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver

async def compile_graph_with_async_checkpointer(graph, graph_name):
    # This function must be async for AsyncMongoClient
    mongodb_client = AsyncMongoClient(os.getenv("MONGODB_URI_LANGGRAPH_CHECKPOINTER"))
    checkpointer = AsyncMongoDBSaver(mongodb_client)

    graph = graph.compile(checkpointer=checkpointer)

    with open(f"./app/workflows/diagrams/{graph_name}.png", "wb") as f:
        f.write(graph.get_graph(xray=0).draw_mermaid_png())

    return graph