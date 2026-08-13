from langchain.tools import tool 
import requests
import re
import json
from rag import search_documents
from urllib import response
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from database_security import (
    validate_select,
    validate_write,
    remove_internal_ids
)
from postgres_tool import (
    get_schema_text as get_postgres_schema_text,
    execute_select as postgres_execute_select,
    execute_write as postgres_execute_write
)
from sqlserver_tool import (
     get_schema_text as get_sqlserver_schema_text,
    execute_select as sqlserver_execute_select,
    execute_write as sqlserver_execute_write
)
# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


@tool
def calculator(a: str, b: str, operation: str) -> str:
    """
    Perform arithmetic calculations.

    operation must be one of:
    add, subtract, multiply, divide.
    """

    a = float(a)
    b = float(b)

    operation = operation.lower().strip()

    if operation == "add":
        result = a + b

    elif operation == "subtract":
        result = a - b

    elif operation == "multiply":
        result = a * b

    elif operation == "divide":

        if b == 0:
            return "Error: Cannot divide by zero."

        result = a / b

    else:
        return (
            "Invalid operation. "
            "Use add, subtract, multiply, or divide."
        )

    # Return integer when result is a whole number
    if result.is_integer():
        return str(int(result))

    return str(result)

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""

    url = f"https://wttr.in/{city}?format=j1"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    current = data["current_condition"][0]

    temperature = current["temp_C"]
    feels_like = current["FeelsLikeC"]
    description = current["weatherDesc"][0]["value"]
    humidity = current["humidity"]

    return (
        f"Weather in {city}: "
        f"{description}, "
        f"{temperature}°C, "
        f"feels like {feels_like}°C, "
        f"humidity {humidity}%."
    )


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    results = DDGS().text(
        query,
        max_results=5
    )
    return str(results)

tavily = TavilySearch(
    max_results=2
)
@tool
def travel_planner(
    destination: str,
    days: str,
    interests: str = ""
) -> str:
    """
    Research current travel information and create research
    for a travel itinerary.

    destination: Travel destination.
    days: Number of days.
    interests: User interests such as beaches, food,
    sightseeing, shopping, history, etc.
    """
    try:
        days_int = int(days)

    except ValueError:
        return "Days must be a valid number."
    
    query = f"""
    Travel planning research for {destination}.
    Create research for a {days_int}-day trip.
    Interests: {interests}

    Find current information about:
    - Best attractions
    - Things to do
    - Recommended restaurants
    - Transportation
    - Hotels or recommended areas to stay
    - Opening hours where relevant
    - Popular activities
    - Practical travel information
    """

    result = tavily.invoke({
        "query": query,
        "topic": "general",
        "search_depth": "advanced"
    })
    return str(result)


@tool
def rag_search(query: str) -> str:
    """
    Search private application documents.

    Supports PDF, TXT, DOCX and CSV files.

    Use this tool when the user asks about
    information contained in the application's
    private documents.
    """
    docs = search_documents(
        query,
        k=4
    )

    if not docs:
        return "No relevant information found."

    results = []

    for doc in docs:

        results.append({
            "content": doc.page_content,
            "source": doc.metadata.get(
                "source",
                "unknown"
            ),
            "page": doc.metadata.get(
                "page",
                ""
            )
        })

    return json.dumps(
        results,
        ensure_ascii=False
    )


@tool
def postgres_search(query: str) -> str:
    """
    Execute a read-only SQL SELECT query against PostgreSQL.
    Internal IDs should not be returned unless
    explicitly requested by the user.
    """
    
    query = query.strip()

    # -----------------------------------------
    # Must be SELECT
    # -----------------------------------------

    if not query.lower().startswith("select"):

        return (
            "Only SELECT queries are allowed."
        )

    # -----------------------------------------
    # Block dangerous SQL
    # -----------------------------------------

    forbidden = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke"
    ]

    query_lower = query.lower()

    for keyword in forbidden:

        if keyword in query_lower:

            return (
                f"SQL operation '{keyword}' "
                "is not allowed."
            )

    # -----------------------------------------
    # Execute
    # -----------------------------------------

    try:

        results = postgres_execute_select(
            query
        )

        if not results:

            return "No records found."

       # return str(results)
        # Remove internal IDs
        cleaned_results = remove_internal_ids(results)

        return json.dumps(
            cleaned_results,
            default=str,
            ensure_ascii=False
        )

    except Exception as e:

        return (
            f"PostgreSQL error: {str(e)}"
        )

@tool
def postgres_write(query: str) -> str:
    """
    Execute INSERT, UPDATE, or DELETE SQL statements
    against PostgreSQL.

    Use this tool only when the user explicitly asks
    to add, modify, or delete database records.
    """

    query = query.strip()

    query_lower = query.lower()

    allowed = (
        query_lower.startswith("insert")
        or query_lower.startswith("update")
        or query_lower.startswith("delete")
    )

    if not allowed:

        return (
            "Only INSERT, UPDATE, and DELETE "
            "queries are allowed."
        )

    forbidden = [
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke"
    ]

    for keyword in forbidden:
        pattern = rf"\b{re.escape(keyword)}\b"
        if re.search(pattern, query_lower):
            return (
                f"SQL operation '{keyword}' "
                "is not allowed."
            )

    try:

        valid, error_message = validate_write(query)
        if not valid:
            return error_message

        affected_rows = postgres_execute_write(query)

        return (
            f"Query executed successfully. "
            f"{affected_rows} row(s) affected."
        )

    except Exception as e:

        return f"PostgreSQL error: {str(e)}"


# =========================================================
# SQL SERVER SEARCH
# =========================================================

@tool
def sqlserver_search(query: str) -> str:
    """
     Search SQL Server data.

    Internal IDs should not be returned unless
    explicitly requested by the user.
    """

    query = query.strip()

    if not query:
        return "SQL query cannot be empty."

    query_lower = query.lower()

    # =====================================================
    # ONLY SELECT
    # =====================================================

    if not query_lower.startswith("select"):

        return (
            "Only SELECT queries are allowed "
            "in sqlserver_search."
        )

    # =====================================================
    # BLOCK DANGEROUS OPERATIONS
    # =====================================================

    forbidden = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke"
    ]

    for keyword in forbidden:

        if keyword in query_lower:

            return (
                f"SQL operation '{keyword}' "
                "is not allowed."
            )

    # =====================================================
    # EXECUTE
    # =====================================================

    try:

        results = sqlserver_execute_select(query)

        if not results:

            return "No records found."

       # return str(results)
        # Remove internal IDs
        cleaned_results = remove_internal_ids(results)

        return json.dumps(
            cleaned_results,
            default=str,
            ensure_ascii=False
        )

    except Exception as e:

        return (
            f"SQL Server error: {str(e)}"
        )


# =========================================================
# SQL SERVER WRITE
# =========================================================

@tool
def sqlserver_write(query: str) -> str:
    """
    Execute INSERT, UPDATE, or DELETE statements
    against SQL Server.

    Use this tool only when the user explicitly asks
    to add, modify, or delete SQL Server records.
    """

    query = query.strip()

    if not query:

        return "SQL query cannot be empty."

    query_lower = query.lower()

    # =====================================================
    # ALLOWED OPERATIONS
    # =====================================================

    allowed = (
        query_lower.startswith("insert")
        or query_lower.startswith("update")
        or query_lower.startswith("delete")
    )

    if not allowed:

        return (
            "Only INSERT, UPDATE, and DELETE "
            "queries are allowed."
        )

    # =====================================================
    # UPDATE MUST HAVE WHERE
    # =====================================================

    if query_lower.startswith("update"):

        if " where " not in query_lower:

            return (
                "UPDATE queries must contain "
                "a WHERE clause."
            )

    # =====================================================
    # DELETE MUST HAVE WHERE
    # =====================================================

    if query_lower.startswith("delete"):

        if " where " not in query_lower:

            return (
                "DELETE queries must contain "
                "a WHERE clause."
            )

    # =====================================================
    # BLOCK DANGEROUS OPERATIONS
    # =====================================================

    forbidden = [
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke"
    ]

    for keyword in forbidden:
        pattern = rf"\b{re.escape(keyword)}\b"

        if re.search(pattern, query_lower):
        #if keyword in query_lower:
            return (
                f"SQL operation '{keyword}' "
                "is not allowed."
            )

    # =====================================================
    # EXECUTE
    # =====================================================

    try:
        valid, error_message = validate_write(query)
        if not valid:
            return error_message
        
        affected_rows = sqlserver_execute_write(query)

        return (
            f"Query executed successfully. "
            f"{affected_rows} row(s) affected."
        )

    except Exception as e:

        return (
            f"SQL Server error: {str(e)}"
        )

