from pydantic import BaseModel, Field
from typing import Annotated, Any
from app.models import CorrectionItem
from langgraph.graph.message import add_messages
from app.models import Stage


first_message = (
    "Hi, I'm your tour assistant! May I introduce how this tour assistant works?"
)


# ===========================================
#                REDUCER FUNCTIONS
# ===========================================
def extend_list(original: list, new: list):
    original.extend(new)
    return original


def update_str(_, new: str):
    return new


# ===========================================
#                    STATE
# ===========================================
class OutputState(BaseModel):
    messages: Annotated[list, add_messages] = [first_message]


class InputState(BaseModel):
    thread_id: str
    input: str
    aboutMe: str = Field(default="")


class OverallState(InputState, OutputState):
    stage: Stage = Stage.INTRODUCTION
    pass
