# ============================================================
# langgraph_checkpointer.py
# ============================================================

import os

from dotenv import load_dotenv
from psycopg import Connection
from langgraph.checkpoint.postgres import PostgresSaver
from postgres_tool import get_connection 

load_dotenv()

# ============================================================
# CREATE CHECKPOINTER
# ============================================================

def get_checkpointer():
 

    checkpointer = PostgresSaver(
        get_connection()
    )

    # --------------------------------------------------------
    # Create LangGraph checkpoint tables
    # --------------------------------------------------------

    checkpointer.setup()

    print(
        "✅ LangGraph PostgreSQL checkpointer initialized."
    )

    return checkpointer
         

# ============================================================
# CLOSE CHECKPOINTER
# ============================================================

def close_checkpointer(
    checkpointer,
    connection
):

    try:

        if connection:
            connection.close()

    except Exception as e:

        print(
            "Checkpointer close error:",
            e
        )