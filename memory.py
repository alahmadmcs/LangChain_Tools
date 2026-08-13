import os

import psycopg
from dotenv import load_dotenv
from langchain_postgres import PostgresChatMessageHistory
from postgres_tool import get_connection

load_dotenv()


def get_chat_history(session_id: str):

    connection = get_connection()

    history = PostgresChatMessageHistory(
        "chat_history",
        session_id,
        sync_connection=connection
    )

    return history, connection