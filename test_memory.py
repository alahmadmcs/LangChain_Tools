import uuid

from memory import get_chat_history


session_id = str(uuid.uuid4())

print("Session ID:", session_id)

history, connection = get_chat_history(
    session_id
)


print("Existing messages:")

for message in history.messages:

    print(
        message.type,
        ":",
        message.content
    )


history.add_user_message(
    "My name is David."
)

history.add_ai_message(
    "Nice to meet you David."
)


print("\nMessages after saving:")

for message in history.messages:

    print(
        message.type,
        ":",
        message.content
    )


connection.close()