from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from typing import Annotated, Any
from langchain_core.messages import AnyMessage
from app.models import Stage
from enum import Enum

# ===========================================
#                VARIABLE SCHEMA
# ===========================================

class ScheduleItemType(str, Enum):
    TERMINAL = "terminal"
    TRANSPORT = "transport"
    WALK = "walk"
    EVENT = "event"
    MUSEUM_GALLERY = "museum_gallery"
    STREETS = "streets"
    HISTORICAL_SITE = "historical_site"
    MEAL = "meal"
    OTHER = "other"
    REMOVE = "remove"

class ScheduleItemTime(BaseModel):
    start_time: str = Field(description="YYYY-MM-DD HH:MM")
    end_time: str | None = Field(description="YYYY-MM-DD HH:MM")

class ScheduleItem(BaseModel):
    id: int
    type: ScheduleItemType
    time: ScheduleItemTime
    location: str
    title: str
    description: str | None = Field(description="Detailed description of the item. (Optional)")
    suggestion: str | None = Field(description="Detailed suggestions regarding the item. (Optional)")


# ===========================================
#                REDUCER FUNCTIONS
# ===========================================
def extend_list(original: list, new: list):
    if len(new) == 1 and new[0] == "RESET_LIST":
        return []
    original.extend(new)
    return original


def insert_schedule(original: list[ScheduleItem], new: list[ScheduleItem]):
    if len(new) == 1 and new[0] == "RESET_LIST":
        return []
    if len(new) > 0:
        for new_item in new:
            id = new_item.id
            for original_item in original:
                if original_item.id == id:
                    if original_item.type == ScheduleItemType.REMOVE:
                        original.remove(original_item)
                    else:
                        original_item = new_item
                    break
            original.append(new_item)
    return original


# ===========================================
#                    STATE
# ===========================================
class InputState(BaseModel):
    input: str = Field(default=None)

    user_id: str = Field(default=None)
    user_name: str = Field(default=None)
    user_email: str = Field(default=None)
    user_interests: list[str] = Field(default_factory=list)
    user_extra_info: str = Field(default=None)

    trip_arrival_date: str = Field(default=None, description="YYYY-MM-DD")
    trip_arrival_time: str = Field(default=None, description="HH:MM")
    trip_arrival_terminal: str = Field(default=None)

    trip_departure_date: str = Field(default=None, description="YYYY-MM-DD")
    trip_departure_time: str = Field(default=None, description="HH:MM")
    trip_departure_terminal: str = Field(default=None)

    trip_start_of_day_at: str = Field(default=None, description="HH:MM")
    trip_end_of_day_at: str = Field(default=None, description="HH:MM")

    trip_location: str = Field(default=None)
    trip_accommodation_location: str = Field(default=None)

    trip_budget: str = Field(default=None)
    trip_theme: str = Field(default=None)
    trip_fixed_schedules: list[ScheduleItem] = Field(default_factory=list)

    trip_free_hours: int = Field(default=None)


class OverallState(InputState):
    current_stage: Stage = Stage.FIRST_GENERATION

    internet_search_result_list: Annotated[list[dict], extend_list] = Field(
        default_factory=list
    )

    schedule_list: Annotated[list[ScheduleItem], insert_schedule] = Field(
        default_factory=list
    )

    updated_trip_information_list: Annotated[list[str], extend_list] = Field(default_factory=list)
