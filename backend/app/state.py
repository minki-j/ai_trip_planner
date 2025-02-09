from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from typing import Annotated, Any
from langchain_core.messages import AnyMessage
from app.models import Stage
from enum import Enum
import datetime

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
    REMOVE = "remove"
    OTHER = "other"

class TimeSlot(BaseModel):
    start_time: datetime.datetime
    end_time: datetime.datetime | None

class ScheduleItem(BaseModel):
    id: int
    type: ScheduleItemType
    time: TimeSlot
    location: str
    title: str
    description: str | None


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


def replace(_, new: Any):
    return new


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


class OverallState(InputState):
    stage: Stage = Stage.FIRST_GENERATION
    previous_state_before_update: str = Field(default=None)

    internet_search_results: Annotated[list[dict], extend_list] = Field(
        default_factory=list
    )

    activities: Annotated[list[dict], extend_list] = Field(default_factory=list)

    schedule: Annotated[list[ScheduleItem], insert_schedule] = Field(
        default_factory=list
    )

    slot_in_schedule_loop_messages: Annotated[list[AnyMessage], add_messages] = Field(default_factory=list)
