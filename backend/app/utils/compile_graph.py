import os

from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import AsyncMongoClient, MongoClient

async def compile_graph_with_async_checkpointer(graph, graph_name):
    mongodb_client = AsyncMongoClient(os.getenv("MONGODB_URI_LANGGRAPH_CHECKPOINTER"))
    checkpointer = AsyncMongoDBSaver(mongodb_client)

    graph = graph.compile(checkpointer=checkpointer)

    with open(f"./app/workflows/diagrams/{graph_name}.png", "wb") as f:
        f.write(graph.get_graph(xray=0).draw_mermaid_png())

    return graph

def compile_graph_with_sync_checkpointer(graph, graph_name):
    mongodb_client = MongoClient(os.getenv("MONGODB_URI_LANGGRAPH_CHECKPOINTER"))
    checkpointer = MongoDBSaver(mongodb_client)

    graph = graph.compile(checkpointer=checkpointer)

    with open(f"./app/workflows/diagrams/{graph_name}.png", "wb") as f:
        f.write(graph.get_graph(xray=1).draw_mermaid_png())

    return graph
