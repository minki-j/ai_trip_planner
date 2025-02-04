from pydantic import BaseModel, Field
from typing import Annotated, Any
from app.models import CorrectionItem
from langgraph.graph.message import add_messages


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
    correctedText: Annotated[str, update_str] = Field(default="")
    corrections: Annotated[list, extend_list] = Field(default_factory=list)
    vocabulary: Annotated[str, update_str] = Field(default="")
    translated_vocabulary: Annotated[str, update_str] = Field(default="")
    definition: Annotated[str, update_str] = Field(default="")
    examples: Annotated[list, extend_list] = Field(default_factory=list)
    breakdown_stream_msg: Annotated[list, add_messages] = Field(default_factory=list)
    breakdown: Annotated[str, update_str] = Field(default="")


class InputState(BaseModel):
    thread_id: str
    input: str
    aboutMe: str = Field(default="")
    englishLevel: str = Field(default="")
    motherTongue: str = Field(default="")


class OverallState(InputState, OutputState):
    pass
