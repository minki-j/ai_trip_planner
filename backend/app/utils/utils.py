from datetime import datetime, timedelta
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from app.state import ScheduleItem, ScheduleItemType


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
    schedule_items: list[ScheduleItem], include_ids: bool = True
) -> str:

    if not schedule_items:
        return "No schedule items are arranged yet."

    schedule_items.sort(key=lambda x: (x.time.start_time))

    result = []
    for item in schedule_items:
        content = (
            f"- ID: {item.id} | Time: {item.time.start_time}"
            if include_ids
            else f"- Time: {item.time.start_time}"
        )

        if item.time.end_time:
            content += f" ~ {item.time.end_time}"

        content += f" | Type: {item.type.value} | Title: {item.title} | Location: {item.location}"

        if item.description:
            content += f" | Description: {item.description}"

        result.append(content)

    return "\n".join(result).strip()


def parse_datetime(dt_str):
    formats = [
        "%Y-%m-%d %H:%M",  # Localized Time
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
        schedule_items[0].type != ScheduleItemType.TERMINAL
        or schedule_items[-1].type != ScheduleItemType.TERMINAL
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
    current_slot: list[datetime, datetime] = [
        overall_start,
        overall_start + slot_duration,
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
        print("calculate_empty_slots: No free slots are available. Returning None.")
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
    dates = set(
        [f"{start.year}-{start.month}-{start.day}" for start, end in merged_slots]
    ).sorted()

    free_slots_grouped_by_date = {}
    for date in dates:
        free_slots_grouped_by_date[date] = []

    for start, end in merged_slots:
        free_slots_grouped_by_date[f"{start.year}-{start.month}-{start.day}"].append(
            f"{start.hour}:{start.minute} ~ {end.hour}:{end.minute}"
        )

    free_slots_string = ""

    for date, slots in free_slots_grouped_by_date.items():
        free_slots_string += (
            f"- {date}: " + ", ".join([(f"{slot}") for slot in slots]) + "\n"
        )

    return free_slots_string
