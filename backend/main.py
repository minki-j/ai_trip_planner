import os
import json
import logging
from typing import Optional
from varname import nameof as n
from fastapi.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError

from fastapi import FastAPI, WebSocket, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
import redis.asyncio as redis
from datetime import timedelta

from langgraph.errors import InvalidUpdateError

from app.state import ScheduleItem, Stage
from app.utils.compile_graph import compile_graph_with_async_checkpointer
from app.workflows.entry_graph import g as entry_graph
from app.workflows.generate_schedule_graph import (
    add_fixed_schedules,
    fill_schedule_loop,
    add_terminal_schedules,
    fill_terminal_transportation_schedule,
    validate_full_schedule_loop,
    fill_schedule_reflection,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.CRITICAL)


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


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: reset Redis
    await redis_client.flushall()
    logger.critical("All Redis keys have been reset")
    yield
    # Shutdown: cleanup if needed

app = FastAPI(title="Trip Planner Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "ws://localhost:3000",
        "https://aitourassistant-production.up.railway.app/",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    logger.info("REDIS_URL not found in environment variables, using localhost")
    redis_url = "redis://localhost:6379"

try:
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    logger.critical(f"Connected to Redis at {redis_url}")

except Exception as e:
    logger.critical(f"Failed to connect to Redis: {str(e)}")
    raise

# Key prefix for Redis
REDIS_KEY_PREFIX = "tour_assistant:ids_in_progress:"

# Time to live for Redis keys
REDIS_TTL = timedelta(minutes=10)


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
            "user_id": user["id"],
            "user_name": user["name"],
            "user_email": user["email"],
        },
    )
    return True


@app.get("/graph_state")
async def get_graph_state(user: dict = Depends(get_current_user_http)):

    if not user:
        return {"error": "No user provided or user not found"}

    # Check if user ID exists in Redis
    if await redis_client.exists(f"{REDIS_KEY_PREFIX}{user['id']}"):
        return {
            "connection_closed": True,
            "error": "The user's schedule is under generation. Please wait until the generation is complete. It may take up to 5 minutes.",
        }

    compiled_entry_graph = await compile_graph_with_async_checkpointer(
        entry_graph, "entry"
    )
    config = {"configurable": {"thread_id": user["id"]}}
    state = await compiled_entry_graph.aget_state(config, subgraphs=True)
    state = state.values

    if not state:
        return None
    return state


@app.post("/update_trip")
async def update_trip(request: Request):
    form_data = await request.json()

    if not form_data:
        return {"error": "No form data provided"}

    # Serialize dictionary to pydantic model
    if "trip_fixed_schedules" in form_data and form_data["trip_fixed_schedules"]:
        parsed_fixed_schedule_dict_list = json.loads(form_data["trip_fixed_schedules"])
        if parsed_fixed_schedule_dict_list:
            form_data["trip_fixed_schedules"] = [
                ScheduleItem.model_validate(fixed_schedule_dict)
                for fixed_schedule_dict in parsed_fixed_schedule_dict_list
            ]
        else:
            form_data["trip_fixed_schedules"] = []
    else:
        form_data["trip_fixed_schedules"] = []

    compiled_entry_graph = await compile_graph_with_async_checkpointer(
        entry_graph, "entry"
    )
    config = {"configurable": {"thread_id": form_data["id"]}}

    #! TODO: Need to keep this variable for modify feature later
    # # get previous state and cache it to previous_state_before_update field
    # previous_state = await compiled_entry_graph.aget_state(config)
    # previous_state = previous_state.values
    # form_data["updated_trip_information"] = ", ".join(
    #     [
    #         f"Trip information on '{key}' was originally '{previous_state[key]}', but updated to '{value}'"
    #         for key, value in form_data.items() if key != "id"
    #     ]
    # )

    # update the state with form data
    try:
        await compiled_entry_graph.aupdate_state(
            config,
            form_data,
        )
    except InvalidUpdateError as e:
        print("Graph is not initialized yet. Invoking with END stage")
        form_data["current_stage"] = Stage.END
        await compiled_entry_graph.ainvoke(
            form_data,
            config,
        )

        await compiled_entry_graph.aupdate_state(
            config=config,
            values={"current_stage": Stage.FIRST_GENERATION},
        )

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

    await compiled_entry_graph.aupdate_state(config, new_schedule_data)

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
        },
    )

    # reset Redis key
    await redis_client.delete(f"{REDIS_KEY_PREFIX}{user['id']}")

    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "State reset successfully"},
    )


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
        send_date_via_websocket = True

        # Add user ID to Redis with TTL
        await redis_client.setex(f"{REDIS_KEY_PREFIX}{user['id']}", REDIS_TTL, "1")
        logger.critical(f"User ID {user['id']} is added to Redis")

        async for graph_namespace, stream_mode, data in workflow.astream(
            {"current_stage": Stage.FIRST_GENERATION},
            stream_mode=["custom", "updates"],
            config={
                "recursion_limit": int(os.environ.get("RECURSION_LIMIT")),
                "configurable": {
                    "thread_id": user["id"],
                },
            },
            subgraphs=True,
        ):
            if not send_date_via_websocket:
                continue

            if stream_mode == "custom":
                data["data_type"] = "reasoning_steps"
                try:
                    await websocket.send_json(data)
                except WebSocketDisconnect:
                    logger.info("WebSocket connection closed by client")
                    send_date_via_websocket = False
                    continue
                except ConnectionClosedError:
                    logger.info("WebSocket connection closed unexpectedly")
                    send_date_via_websocket = False
                    continue
                except Exception as e:
                    logger.error(f"Error sending data via websocket: {str(e)}")
                    break
            else:
                if update_dict := (
                    data.get(n(add_fixed_schedules))
                    or data.get(n(add_terminal_schedules))
                    or data.get(n(fill_schedule_loop))
                    or data.get(n(fill_schedule_reflection))
                    or data.get(n(fill_terminal_transportation_schedule))
                    or data.get(n(validate_full_schedule_loop))
                ):
                    for schedule in update_dict["schedule_list"]:
                        try:
                            await websocket.send_json(
                                {**schedule.model_dump(), "data_type": "schedule"}
                            )
                        except WebSocketDisconnect:
                            logger.info("WebSocket connection closed by client")
                            send_date_via_websocket = False
                            continue
                        except ConnectionClosedError:
                            logger.info("WebSocket connection closed unexpectedly")
                            send_date_via_websocket = False
                            continue
                        except Exception as e:
                            logger.error(
                                f"Error sending schedule via websocket: {str(e)}"
                            )
                            break

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print("Error on ws/generate_schedule: ", error_trace)
    finally:
        try:
            await websocket.close()
        except Exception as e:
            pass
        await redis_client.delete(f"{REDIS_KEY_PREFIX}{user['id']}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
