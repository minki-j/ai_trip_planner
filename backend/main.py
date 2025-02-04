from fastapi import FastAPI, HTTPException, WebSocket, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from contextlib import asynccontextmanager

from bson import ObjectId
from langchain_core.messages import AnyMessage
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from app.db.mongodb import ping_mongodb, main_db
from app.utils.compile_graph import compile_graph_with_async_checkpointer

# from app.models import

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.llm import chat_model

from app.workflows.entry_graph import g as entry_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ping_mongodb()
    yield


async def get_current_user_websocket(websocket: WebSocket) -> Optional[dict]:
    # For WebSocket connections, we'll get the user_id from the query parameters
    user_id = websocket.query_params.get("user_id")
    if user_id:
        user = await main_db.users.find_one({"googleId": user_id})
        if user:
            return {
                "id": user_id,
                "aboutMe": user.get("aboutMe", ""),
            }
    return None


async def get_current_user_http(request: Request) -> Optional[dict]:
    # For HTTP requests, we'll get the user_id from the request headers
    user_id = request.query_params.get("user_id")
    if user_id:
        user = await main_db.users.find_one({"googleId": user_id})
        if user:
            return {
                "id": user_id,
                "aboutMe": user.get("aboutMe", ""),
            }
    return None


app = FastAPI(title="Tour Assistant Backend", lifespan=lifespan)

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


@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    """
    Process chat messages.
    """
    try:
        await websocket.accept()
        user = await get_current_user_websocket(websocket)
        if not user:
            await websocket.send_json(
                {"error": "No user ID provided or user not found"}
            )
            await websocket.close()
            return

        data = await websocket.receive_json()

        input = data.get("input")

        if not input:
            error_msg = "No text provided"
            await websocket.send_json({"error": error_msg})
            return

        workflow = await compile_graph_with_async_checkpointer(entry_graph, "entry")

        async for stream_mode, data in workflow.astream(
            {
                "input": input,
                "thread_id": user["id"],
                "aboutMe": user.get("aboutMe", ""),
            },
            stream_mode=["custom", "updates"],
            config={"configurable": {"thread_id": user["id"]}},
        ):
            if stream_mode == "custom":
                print("\n\ncustom: ", data)
                pass
            elif stream_mode == "updates":
                print("\n\nupdates: ", data)
                data = next(iter(data.values()))  # skip the graph name
                if data.get("messages") is not None and hasattr(
                    data["messages"][0], "content"
                ):
                    data = {
                        "role": "Assistant",
                        "message": data["messages"][0].content,
                    }

            await websocket.send_json(data)

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print("Error on ws/correction: ", error_trace)
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
