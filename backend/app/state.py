from pydantic import BaseModel, Field
from typing import Annotated, Any
from langchain_core.messages import AIMessage
from app.models import Stage


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
    messages: Annotated[list, extend_list] = Field(default_factory=list)


class InputState(BaseModel):
    input: str = Field(default=None)
    user_id: str = Field(default=None)
    user_name: str = Field(default=None)
    user_email: str = Field(default=None)
    user_interests: list[str] = Field(default_factory=list)
    user_extra_info: str = Field(default=None)

    trip_transportation_schedule: list[str] = Field(default_factory=list)
    trip_location: str = Field(default=None)
    trip_duration: str = Field(default=None)
    trip_budget: str = Field(default=None)
    trip_theme: str = Field(default=None)
    trip_fixed_schedules: list[str] = Field(default_factory=list)


class OverallState(InputState, OutputState):
    stage: Stage = Stage.INQUIRY


