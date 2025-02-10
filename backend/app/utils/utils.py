from langchain_core.messages import AnyMessage, HumanMessage, AIMessage

from app.state import ScheduleItem, ScheduleItemType, TimeSlot


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


def convert_schedule_items_to_string(schedule_items: list[ScheduleItem]) -> str:

    schedule_items.sort(key=lambda x: (x.time.start_time))

    result = []
    for item in schedule_items:
        content = f"- ID:{item.id} | Time:{item.time.start_time}"
        
        if item.time.end_time:
            content += f"~{item.time.end_time}"
        
        content += f" | Type:{item.type.value} | Title:{item.title} | Location:{item.location}"

        if item.description:
            content += f" | Description:{item.description}"

        result.append(content)

    return "\n".join(result).strip() or "NO SCHEDULE ITEMS PROVIDED!"
