import os
import json
from typing import Optional
from varname import nameof as n

from fastapi import FastAPI, HTTPException, WebSocket, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.llms import chat_model
from app.models import Stage
from app.utils.compile_graph import compile_graph_with_async_checkpointer
from app.workflows.entry_graph import g as entry_graph
from app.workflows.generate.graph import (
    add_fixed_schedules,
    slot_in_schedule_loop,
    add_terminal_schedules,
)


async def get_current_user_websocket(websocket: WebSocket) -> Optional[dict]:
    # For WebSocket connections, we'll get the user_id from the query parameters
    user_id = websocket.query_params.get("user_id")
    return {
        "id": user_id,
    }


async def get_current_user_http(request: Request) -> Optional[dict]:
    # For HTTP requests, we'll get the user_id from the request headers
    user_id = request.query_params.get("user_id")
    return {
        "id": user_id,
    }


app = FastAPI(title="Tour Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "ws://localhost:3000",
        # "https://backend-production-c134.up.railway.app",
        # "https://englishtutor-production.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}


@app.post("/add_user")
async def add_user(request: Request):
    user = await request.json()

    if not user:
        return {"error": "No user provided"}
    compiled_entry_graph = await compile_graph_with_async_checkpointer(
        entry_graph, "entry"
    )
    config = {"configurable": {"thread_id": user["id"]}}
    await compiled_entry_graph.aupdate_state(
        config,
        {
            "user_name": user["name"],
            "user_id": user["id"],
            "user_email": user["email"],
        },
    )
    return True


@app.post("/update_trip")
async def update_trip(request: Request):
    form_data = await request.json()

    if not form_data:
        return {"error": "No form data provided"}

    # convert string to list
    if "user_interests" in form_data:
        form_data["user_interests"] = [
            item.strip()
            for item in form_data["user_interests"].split(",")
            if item.strip()
        ]
    if "trip_fixed_schedules" in form_data:
        form_data["trip_fixed_schedules"] = [
            schedule.strip()
            for schedule in form_data["trip_fixed_schedules"].split("\n")
            if schedule.strip()
        ]

    compiled_entry_graph = await compile_graph_with_async_checkpointer(
        entry_graph, "entry"
    )
    config = {"configurable": {"thread_id": form_data["id"]}}

    # get previous state and cache it to previous_state_before_update field
    previous_state = await compiled_entry_graph.aget_state(config)
    previous_state = previous_state.values

    #! TODO: Nedd to keep this variable for modify feature later
    # form_data["updated_trip_information"] = ", ".join(
    #     [
    #         f"Trip information on '{key}' was originally '{previous_state[key]}', but updated to '{value}'"
    #         for key, value in form_data.items() if key != "id"
    #     ]
    # )

    # update the state with form data
    await compiled_entry_graph.aupdate_state(config, form_data)
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Trip updated successfully"},
    )


@app.post("/update_schedule")
async def update_schedule(
    request: Request, user: dict = Depends(get_current_user_http)
):
    new_schedule_data = await request.json()

    if not new_schedule_data:
        return {"error": "No form data provided"}

    compiled_entry_graph = await compile_graph_with_async_checkpointer(
        entry_graph, "entry"
    )
    config = {"configurable": {"thread_id": user["id"]}}

    # update the state with form data
    result = await compiled_entry_graph.aupdate_state(config, new_schedule_data)
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Schedule updated successfully"},
    )


@app.delete("/reset_state")
async def reset_state(user: dict = Depends(get_current_user_http)):
    compiled_entry_graph = await compile_graph_with_async_checkpointer(
        entry_graph, "entry"
    )
    config = {"configurable": {"thread_id": user["id"]}}

    # update the state with form data
    await compiled_entry_graph.aupdate_state(
        config,
        {
            "stage": Stage.FIRST_GENERATION,
            "internet_search_result_list": ["RESET_LIST"],
            "schedule_list": ["RESET_LIST"],
            # "updated_trip_information_list": ["RESET_LIST"],
        },
    )

    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "State reset successfully"},
    )


@app.get("/graph_state")
async def get_graph_state(user: dict = Depends(get_current_user_http)):

    if not user:
        return {"error": "No user provided or user not found"}

    compiled_entry_graph = await compile_graph_with_async_checkpointer(
        entry_graph, "entry"
    )
    config = {"configurable": {"thread_id": user["id"]}}
    state = await compiled_entry_graph.aget_state(config, subgraphs=True)
    state = state.values
    # print(f"\n\n>>> GRAPH STATE:\n{state}\n\n")

    if not state:
        return None
    return state


@app.websocket("/ws/generate_schedule")
async def generate_schedule_ws(websocket: WebSocket):
    try:
        await websocket.accept()
        user = await get_current_user_websocket(websocket)
        if not user:
            await websocket.send_json(
                {"error": "No user ID provided or user not found"}
            )
            await websocket.close()
            return

        workflow = await compile_graph_with_async_checkpointer(entry_graph, "entry")

        async for graph_namespace, stream_mode, data in workflow.astream(
            {"input": "!! This message is just to avoid empty graph invocation."},
            stream_mode=["custom", "updates"],
            config={
                "recursion_limit": int(os.environ.get("RECURSION_LIMIT")),
                "configurable": {
                    "thread_id": user["id"],
                },
            },
            subgraphs=True,
        ):
            if stream_mode == "custom":
                data["data_type"] = "reasoning_steps"
                await websocket.send_json(data)
            else:
                if update_dict := (
                    data.get(n(add_fixed_schedules))
                    or data.get(n(add_terminal_schedules))
                    or data.get(n(slot_in_schedule_loop))
                ):
                    for schedule in update_dict["schedule_list"]:
                        await websocket.send_json(
                            {**schedule.model_dump(), "data_type": "schedule"}
                        )

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print("Error on ws/generate_schedule: ", error_trace)
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
