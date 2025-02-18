from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field
from app.models import Stage


# ===========================================
#                VARIABLE SCHEMA
# ===========================================
class ScheduleItemType(str, Enum):
    TERMINAL = "terminal"
    TRANSPORT = "transport"
    WALK = "walk"
    MEAL = "meal"
    EVENT = "event"
    STREETS = "streets"
    MUSEUM_GALLERY = "museum_gallery"
    HISTORICAL_SITE = "historical_site"
    OTHER = "other"
    REMOVE = "remove"


class ScheduleItemTime(BaseModel):
    start_time: str = Field(
        description="Full date-and-time should be included. e.g. 'YYYY-MM-DD HH:MM'"
    )
    end_time: str | None = Field(
        description="Both full-date-and-time and time-only are allowed. e.g. 'YYYY-MM-DD HH:MM' or 'HH:MM'"
    )


class ScheduleItem(BaseModel):
    id: int
    activity_type: ScheduleItemType
    time: ScheduleItemTime
    location: str
    title: str
    description: str | None = Field(description="A brief description of the schedule.")
    suggestion: str | None = Field(
        description="Detailed suggestions or tips for the schedule."
    )


# ===========================================
#                REDUCER FUNCTIONS
# ===========================================
def extend_list(original: list, new: list):
    if len(new) == 1 and new[0] == "RESET_LIST":
        return []
    original.extend(new)
    return original


def insert_schedules(original: list[ScheduleItem], new: list[ScheduleItem]):
    if len(new) == 1 and new[0] == "RESET_LIST":
        return []
    if len(new) > 0:
        for new_item in new:
            found = False
            for i, original_item in enumerate(original):
                if original_item.id == new_item.id:
                    found = True
                    if new_item.activity_type == ScheduleItemType.REMOVE:
                        original.pop(i)
                    else:
                        original[i] = new_item
                    break
            if not found:
                original.append(new_item)
    return original


# ===========================================
#                    STATE
# ===========================================
class InputState(BaseModel):
    input: str = Field(default=None)
    current_stage: Stage = Stage.FIRST_GENERATION

    user_id: str = Field(default=None)
    user_name: str = Field(default=None)
    user_email: str = Field(default=None)
    user_interests: str = Field(default=None)
    user_extra_info: str = Field(default=None)

    trip_arrival_date: str = Field(default=None, description="YYYY-MM-DD")
    trip_arrival_time: str = Field(default=None, description="HH:MM")
    trip_arrival_terminal: str = Field(default=None)

    trip_departure_date: str = Field(default=None, description="YYYY-MM-DD")
    trip_departure_time: str = Field(default=None, description="HH:MM")
    trip_departure_terminal: str = Field(default=None)

    trip_location: str = Field(default=None)
    trip_accommodation_location: str = Field(default=None)

    trip_budget: str = Field(default=None)
    trip_theme: str = Field(default=None)

    trip_start_of_day_at: str = Field(default=None, description="HH:MM")
    trip_end_of_day_at: str = Field(default=None, description="HH:MM")

    trip_fixed_schedules: list[ScheduleItem] = Field(default_factory=list)

    trip_free_hours: int = Field(default=None)


class OverallState(InputState):
    internet_search_result_list: Annotated[list[dict], extend_list] = Field(
        default_factory=list
    )

    schedule_list: Annotated[list[ScheduleItem], insert_schedules] = Field(
        default_factory=list
    )
