from memory import get_connection
from langchain_postgres import PostgresChatMessageHistory


connection = get_connection()

PostgresChatMessageHistory.create_tables(
    connection,
    "chat_history"
)

connection.close()

print("Chat history table created successfully.")