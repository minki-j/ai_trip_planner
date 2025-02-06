from pydantic import BaseModel, Field
from typing import Annotated, Any
from app.models import CorrectionItem
from langgraph.graph.message import add_messages
from app.models import Stage
from langchain_core.messages import AIMessage


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
    messages: Annotated[list, add_messages] = Field(default_factory=list)

class InputState(BaseModel):
    thread_id: str
    input: str
    user_name: str = Field(default="unknown")
    trip_location: str = Field(default="unknown")
    trip_date: str = Field(default="unknown")
    about_me: str = Field(default="unknown")


class OverallState(InputState, OutputState):
    stage: Stage = Stage.INTRODUCTION
    
    intro_rationale: str = ""
    intro_reply: str = ""
