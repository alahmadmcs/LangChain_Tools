
# ============================================================
# app.py
# ============================================================

import os

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI

from Tools.agent_tools import (
    calculator,
    get_weather,
    travel_planner,
    web_search,
    rag_search,
    postgres_search,
    postgres_write,
    sqlserver_search,
    sqlserver_write,
)

from postgres_tool import (
    get_schema_text as get_postgres_schema_text,
)

from sqlserver_tool import (
    get_schema_text as get_sqlserver_schema_text,
)

from agent_graph import ask_agent


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# LLM
# ============================================================

llm = ChatOpenAI(
    model="openai/gpt-oss-120b",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0,
)


# ============================================================
# DATABASE SCHEMAS
# ============================================================

postgres_schema = get_postgres_schema_text()

sqlserver_schema = get_sqlserver_schema_text()


# ============================================================
# TOOLS
# ============================================================

tools = [

    calculator,

    web_search,

    get_weather,

    travel_planner,

    rag_search,

    postgres_search,

    postgres_write,

    sqlserver_search,

    sqlserver_write,

]


# ============================================================
# BIND TOOLS TO MODEL
# ============================================================

model_with_tools = llm.bind_tools(
    tools
)


# ============================================================
# ASK AGENT
# ============================================================

def run_agent(
    user_input: str,
    session_id: str,
):

    return ask_agent(

        user_input=user_input,

        session_id=session_id,

        model_with_tools=model_with_tools,

        tools=tools,

        postgres_schema=postgres_schema,

        sqlserver_schema=sqlserver_schema,

    )

