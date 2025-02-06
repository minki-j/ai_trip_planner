from langchain_core.messages import AnyMessage, HumanMessage, AIMessage

def convert_messages_to_string(messages: AnyMessage) -> str:
    return "\n".join([f"{"User" if isinstance(msg, HumanMessage) else "Assistant"}: {msg.content}" for msg in messages]).strip() or "NO MESSAGES PROVIDED!"
