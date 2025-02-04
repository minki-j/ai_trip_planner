from fastapi import FastAPI, HTTPException, WebSocket, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocketDisconnect
from contextlib import asynccontextmanager

from bson import ObjectId
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

from app.db.mongodb import ping_mongodb, main_db
from app.utils.compile_graph import compile_graph_with_async_checkpointer
# from app.models import

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.llm import chat_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ping_mongodb()
    yield


class UserMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get user_id from request headers or query parameters
        user_id = request.headers.get("user-id") or request.query_params.get("user_id")

        if user_id:
            # Fetch user info from database
            user = await main_db.users.find_one({"googleId": user_id})
            if user:
                # Add user info to request state
                request.state.user = {
                    "id": user_id,
                    "aboutMe": user.get("aboutMe", ""),
                    "englishLevel": user.get("englishLevel", ""),
                    "motherTongue": user.get("motherTongue", ""),
                }
            else:
                request.state.user = None
        else:
            request.state.user = None

        response = await call_next(request)
        return response


async def get_current_user_websocket(websocket: WebSocket) -> Optional[dict]:
    # For WebSocket connections, we'll get the user_id from the query parameters
    user_id = websocket.query_params.get("user_id")
    if user_id:
        user = await main_db.users.find_one({"googleId": user_id})
        if user:
            return {
                "id": user_id,
                "aboutMe": user.get("aboutMe", ""),
                "englishLevel": user.get("englishLevel", ""),
                "motherTongue": user.get("motherTongue", ""),
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
                "englishLevel": user.get("englishLevel", ""),
                "motherTongue": user.get("motherTongue", ""),
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

app.add_middleware(UserMiddleware)


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
        print("\n\nuser: ", user)
        if not user:
            await websocket.send_json(
                {"error": "No user ID provided or user not found"}
            )
            await websocket.close()
            return

        data = await websocket.receive_json()
        print("\n\ndata: ", data)

        input = data.get("input")

        if not input:
            error_msg = "No text provided"
            await websocket.send_json({"error": error_msg})
            return

        graph = main_graph
        result = Correction(userId=user["id"], input=input)
        workflow = await compile_graph_with_async_checkpointer(graph, type)

        result_id = result.id
        result_id_str = str(result_id)

        async for stream_mode, data in workflow.astream(
            {
                "input": input,
                "thread_id": result_id_str,
                "aboutMe": user.get("aboutMe", ""),
            },
            stream_mode=["custom"],
            config={"configurable": {"thread_id": result_id_str}},
        ):
            response_data = {
                "id": result_id_str,
                "type": type,
            }
            if "correctedText" in data.keys():
                correctedText = data["correctedText"]
                result.correctedText = correctedText
                response_data["correctedText"] = correctedText

            if "correction" in data.keys():
                correction = data["correction"]
                result.corrections.append(correction)
                response_data["correction"] = correction.model_dump()

            await websocket.send_json(response_data)

        result_dict = result.model_dump()
        result_dict["_id"] = result_dict.pop("id")
        await main_db.results.insert_one(result_dict)
    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print("Error on ws/correction: ", error_trace)
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
