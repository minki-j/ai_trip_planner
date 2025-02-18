from datetime import datetime, timedelta
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from app.state import ScheduleItem, ScheduleItemType, OverallState


def convert_messages_to_string(messages: AnyMessage) -> str:
    return (
        "\n".join(
            [
                f"{"User" if isinstance(msg, HumanMessage) else "Assistant"}: {msg.content}"
                for msg in messages
            ]
        ).strip()
        or "NO MESSAGES PROVIDED!"
    )


def convert_schedule_items_to_string(
    schedule_items: list[ScheduleItem],
    include_ids: bool,
    include_description: bool,
    include_suggestion: bool,
    include_heading: bool = True,
) -> str:

    if not schedule_items:
        return "No schedule items are arranged yet."

    schedule_items = sorted(schedule_items, key=lambda x: x.time.start_time)

    result = [
        f" {"ID | " if include_ids else ""}Time | Type | Title | Location{" | Description" if include_description else ""} {" | Suggestion" if include_suggestion else ""}"
    ]  # Only include field names at top to save tokens.
    for item in schedule_items:
        content = (
            f"- {item.id} | {item.time.start_time}"
            if include_ids
            else f"- {item.time.start_time}"
        )

        if item.time.end_time:
            if item.time.end_time.split(" ")[0] == item.time.start_time.split(" ")[0]:
                # Exclude date info if they are the same
                content += f" ~ {item.time.end_time.split(' ')[1]}"
            else:
                content += f" ~ {item.time.end_time}"

        content += f" | {item.activity_type.value} | {item.title} | {item.location}"

        if include_description and item.description:
            content += f" | {item.description}"

        if include_suggestion and item.suggestion:
            content += f" | {item.suggestion}"

        if item.id > 900:
            content += (
                "  (This is a fixed schedule that the user provided. Don't modify it.)"
            )

        result.append(content)

    return "\n".join(result).strip()


def parse_datetime(dt_str):
    formats = [
        "%Y-%m-%d %H:%M",  # Localized Time
        "%H:%M",  # Time only
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse datetime string: {dt_str}")


def calculate_empty_slots(
    schedule_items: list[ScheduleItem],
    trip_start_of_day_at: str,
    trip_end_of_day_at: str,
) -> str:
    if not schedule_items:
        print("\n\nWarning: Schedule_items is not provided.\n\n")
        return None

    start_of_day_hour, start_of_day_minute = [
        int(x) for x in trip_start_of_day_at.split(":")
    ]
    end_of_day_hour, end_of_day_minute = [int(x) for x in trip_end_of_day_at.split(":")]

    schedule_items.sort(key=lambda x: (x.time.start_time))

    if (
        schedule_items[0].activity_type != ScheduleItemType.TERMINAL
        or schedule_items[-1].activity_type != ScheduleItemType.TERMINAL
    ):
        print("\n\nWarning: First and last items must be terminals.\n\n")
        return None

    intervals = []

    for item in schedule_items:
        # Parse the start_time string.
        start = parse_datetime(item.time.start_time)
        # If end_time is not provided, set it to the same as start_time.
        if item.time.end_time is None:
            end = start
        else:
            end = parse_datetime(item.time.end_time)

        intervals.append((start, end))

    # Now create a list of all 30-minute slots between overall_start and overall_end.
    free_slots = []
    overall_start, overall_end = intervals[0][0], intervals[-1][1]
    slot_duration = timedelta(minutes=30)

    # Round up to the next half hour for the start time
    minutes = overall_start.minute
    if minutes > 30:
        adjusted_start = overall_start.replace(
            minute=0, second=0, microsecond=0
        ) + timedelta(hours=1)
    elif minutes > 0 and minutes <= 30:
        adjusted_start = overall_start.replace(minute=30, second=0, microsecond=0)
    else:
        adjusted_start = overall_start.replace(minute=0, second=0, microsecond=0)

    current_slot: list[datetime, datetime] = [
        adjusted_start,
        adjusted_start + slot_duration,
    ]

    while current_slot[1] <= overall_end:
        current_slot_start: datetime = current_slot[0]
        current_slot_end: datetime = current_slot[1]

        # Need an adjusted end hour if it's past midnight. Only used for the third comparision in the if statement below.
        current_slot_end_hour_adjusted = (
            current_slot_end.hour + 24
            if current_slot_end.hour < start_of_day_hour
            else current_slot_end.hour
        )

        # Users have set when to start the day and when to end the day. If the current slot is not in that range, skip it.
        if (
            not start_of_day_hour <= current_slot_start.hour
            or (
                start_of_day_hour == current_slot_start.hour
                and not start_of_day_minute <= current_slot_start.minute
            )
            or not current_slot_end_hour_adjusted <= end_of_day_hour
            or (
                current_slot_end.hour == end_of_day_hour
                and not current_slot_end.minute <= end_of_day_minute
            )
        ):
            current_slot = [
                current_slot[0] + slot_duration,
                current_slot[1] + slot_duration,
            ]
            continue

        is_free = True
        for start, end in intervals:
            if current_slot[0] < end and current_slot[1] > start:
                is_free = False
                break

        if is_free:
            # Append the slot's starting time as a tuple.
            free_slots.append(current_slot)

        # Move to the next 30-minute slot.
        current_slot = [
            current_slot[0] + slot_duration,
            current_slot[1] + slot_duration,
        ]
    if not free_slots:
        print("calculate_empty_slots: No free slots are available.")
        return None

    # lump together free slots that are next to each other
    free_slots.sort(key=lambda x: x[0])
    merged_slots = [free_slots[0]]
    for current_slot in free_slots[1:]:
        last_slot = merged_slots[-1]
        if current_slot[0] <= last_slot[1]:
            last_slot[1] = current_slot[1]
        else:
            merged_slots.append(current_slot)

    # group to the same date
    dates = sorted(
        set([f"{start.year}-{start.month}-{start.day}" for start, end in merged_slots])
    )

    free_slots_grouped_by_date = {}
    for date in dates:
        free_slots_grouped_by_date[date] = []

    for start, end in merged_slots:
        free_slots_grouped_by_date[f"{start.year}-{start.month}-{start.day}"].append(
            f"{str(start.hour).zfill(2)}:{str(start.minute).zfill(2)} ~ {str(end.hour).zfill(2)}:{str(end.minute).zfill(2)}"
        )

    free_slots_string = ""

    for date, slots in free_slots_grouped_by_date.items():
        free_slots_string += (
            f"- {date}: " + ", ".join([(f"{slot}") for slot in slots]) + "\n"
        )

    return free_slots_string


def calculate_trip_free_hours(
    trip_arrival_date: str,
    trip_arrival_time: str,
    trip_departure_date: str,
    trip_departure_time: str,
    trip_start_of_day_at: str,
    trip_end_of_day_at: str,
    trip_fixed_schedules: list[ScheduleItem],
) -> int:
    """Calculate free hours during the trip, accounting for arrival/departure times and fixed schedules.
    """
    # Parse trip dates and times
    arrival_dt = datetime.strptime(f"{trip_arrival_date} {trip_arrival_time}", "%Y-%m-%d %H:%M")
    departure_dt = datetime.strptime(f"{trip_departure_date} {trip_departure_time}", "%Y-%m-%d %H:%M")

    # Parse daily start/end times
    start_of_day = datetime.strptime(trip_start_of_day_at, "%H:%M").time()
    end_of_day = datetime.strptime(trip_end_of_day_at, "%H:%M").time()

    # Initialize result dictionary
    free_hours = {}
    total_free_hours = 0

    # Calculate days between arrival and departure
    current_date = arrival_dt.date()
    while current_date <= departure_dt.date():
        day_start = datetime.combine(current_date, start_of_day)
        day_end = datetime.combine(current_date, end_of_day)

        # Handle arrival day
        if current_date == arrival_dt.date():
            day_start = arrival_dt

        # Handle departure day
        if current_date == departure_dt.date():
            day_end = departure_dt

        # Calculate initial free hours for the day
        free_minutes = (day_end - day_start).total_seconds() / 60

        # Deduct fixed schedules for this day
        for schedule in trip_fixed_schedules:
            schedule_start = datetime.strptime(schedule.time.start_time, "%Y-%m-%d %H:%M")

            # Handle end time (could be full datetime or just time)
            if schedule.time.end_time:
                if len(schedule.time.end_time) <= 5:  # Format: HH:MM
                    end_time = datetime.strptime(schedule.time.end_time, "%H:%M").time()
                    schedule_end = datetime.combine(schedule_start.date(), end_time)
                else:  # Format: YYYY-MM-DD HH:MM
                    schedule_end = datetime.strptime(schedule.time.end_time, "%Y-%m-%d %H:%M")
            else:
                # If no end time, assume 1 hour duration
                schedule_end = schedule_start + timedelta(hours=1)

            # Check if schedule overlaps with current day
            if (schedule_start.date() == current_date and 
                schedule_start >= day_start and 
                schedule_end <= day_end):
                overlap_minutes = (schedule_end - schedule_start).total_seconds() / 60
                free_minutes -= overlap_minutes

        # Convert to hours and store result
        free_hours[current_date.strftime("%Y-%m-%d")] = round(free_minutes / 60, 2)
        total_free_hours += free_hours[current_date.strftime("%Y-%m-%d")]

        current_date += timedelta(days=1)

    return round(total_free_hours, 2)

