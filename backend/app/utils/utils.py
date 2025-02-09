from langchain_core.messages import AnyMessage, HumanMessage, AIMessage

from app.state import ScheduleItem, ScheduleItemType, TimeSlot

def convert_messages_to_string(messages: AnyMessage) -> str:
    return "\n".join([f"{"User" if isinstance(msg, HumanMessage) else "Assistant"}: {msg.content}" for msg in messages]).strip() or "NO MESSAGES PROVIDED!"


def convert_schedule_item_to_string(schedule_items: list[ScheduleItem]) -> str:

    schedule_items.sort(
        key=lambda x: (x.time.start_time)
    )

    result = []
    for item in schedule_items:
        result.append(
            f"- {item.time.start_time} - {item.time.end_time} | {item.type.value} | {item.title} | {item.description}"
        )

    return "\n\n".join(result).strip() or "NO SCHEDULE ITEMS PROVIDED!"
