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

    trip_arrival_date: str = Field(default=None)
    trip_arrival_time: str = Field(default=None)
    trip_arrival_terminal: str = Field(default=None)

    trip_departure_date: str = Field(default=None)
    trip_departure_time: str = Field(default=None)
    trip_departure_terminal: str = Field(default=None)

    trip_start_of_day_at: str = Field(default=None)
    trip_end_of_day_at: str = Field(default=None)

    trip_location: str = Field(default=None)
    trip_accomodation_location: str = Field(default=None)

    trip_budget: str = Field(default=None)
    trip_theme: str = Field(default=None)
    trip_fixed_schedules: list[str] = Field(default_factory=list)

    trip_free_hours: int = Field(default=None)


class OverallState(InputState, OutputState):
    stage: Stage = Stage.FIRST_GENERATION
    how_many_schedules: int = Field(default=10, description="The total number of events or places that the user would visit. This number is calculated based on the free time of the user")
    previous_state_before_update: str = Field(default=None)

    # queries_for_internet_search: list[str] = Field(default_factory=list)
    internet_search_results: Annotated[list[dict], extend_list] = Field(
        default_factory=list
    )


    activities: Annotated[list[dict], extend_list] = Field(default_factory=list)
    reasoning_steps: Annotated[list[dict], extend_list] = Field(default_factory=list)