import os
from urllib import response
from dotenv import load_dotenv
from langchain_core import messages
from langchain_groq import ChatGroq
from langchain.tools import tool 
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage,ToolMessage
from ddgs import DDGS
import requests
from langchain_tavily import TavilySearch
import json
from rag import search_documents
from postgres_tool import (
    get_schema_text,
    execute_select,
    execute_write
)

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)

database_schema = get_schema_text()

#print(database_schema)

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
    days: int,
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

    query = f"""
    Travel planning research for {destination}.
    Create research for a {days}-day trip.
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

    Use this tool when the user asks questions about
    data stored in the PostgreSQL database.

    Only SELECT queries are allowed.
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

        results = execute_select(
            query
        )

        if not results:

            return "No records found."

        return str(results)

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

        if keyword in query_lower:

            return (
                f"SQL operation '{keyword}' "
                "is not allowed."
            )

    try:

        affected_rows = execute_write(query)

        return (
            f"Query executed successfully. "
            f"{affected_rows} row(s) affected."
        )

    except Exception as e:

        return f"PostgreSQL error: {str(e)}"

    
tools = [calculator, web_search, get_weather, travel_planner, rag_search, postgres_search, postgres_write]

tool_names = [tool.name for tool in tools]
tools_by_name = {tool.name: tool for tool in tools}

model_with_tools = llm.bind_tools(tools)
# ============================================================ # Main function called by Streamlit 

def ask_agent(user_input: str): 
    messages = [ 
        SystemMessage( 
         content=f"""
               You are a helpful AI assistant.

                    You have access to these tools:

                    - calculator
                    - rag_search
                    - duckduckgo_search
                    - travel_planner
                    - postgres_search
                    - postgres_write

                    ==================================================
                    DATABASE SCHEMA
                    ==================================================

                    {database_schema}

                    ==================================================
                    DATABASE RULES
                    ==================================================

                    When the user asks about PostgreSQL data:

                    READ / SEARCH
                    -------------
                    Use postgres_search.

                    postgres_search is used ONLY for SELECT queries.

                    Examples:

                    "Show all customers"
                    "How many employees are there?"
                    "Show completed orders"
                    "Which customer spent the most?"


                    WRITE / MODIFY
                    --------------
                    Use postgres_write.

                    postgres_write is used for:

                    - INSERT
                    - UPDATE
                    - DELETE

                    Examples:

                    "Add a new customer"
                    "Change David's country to UAE"
                    "Update employee salary"
                    "Delete customer David"


                    ==================================================
                    IMPORTANT DATABASE RULES
                    ==================================================

                    1. Never guess table names.

                    2. Never guess column names.

                    3. Use the provided database schema.

                    4. Use PostgreSQL-compatible SQL.

                    5. Use JOINs when information exists
                    across multiple tables.

                    6. Use aliases for readability.

                    7. postgres_search MUST ONLY execute SELECT.

                    8. postgres_write MUST ONLY execute
                    INSERT, UPDATE, or DELETE.

                    9. UPDATE must always contain a WHERE clause.

                    10. DELETE must always contain a WHERE clause.

                    11. Never execute DROP, ALTER, TRUNCATE,
                        CREATE, GRANT, or REVOKE.

                    12. Never modify the database unless the
                        user explicitly requests a modification.


                    ==================================================
                    IMPORTANT ORDER RELATIONSHIPS
                    ==================================================

                    orders.customer_id → customers.id

                    order_items.order_id → orders.id

                    order_items.product_id → products.id


                    ==================================================
                    ORDER QUERY RULES
                    ==================================================

                    Use:

                    orders

                    when the question is about:

                    - order status
                    - order date
                    - order total
                    - order ID


                    Use:

                    customers + orders

                    when the user asks about:

                    - customers and orders
                    - customer order history
                    - customer spending

                    Use:

                    orders + order_items + products

                    when the user asks about:

                    - products in orders
                    - products purchased
                    - quantities purchased

                    Use:

                    customers + orders + order_items + products

                    when the user asks:

                    - which customer bought which product
                    - customer purchase history
                    - customer/product/order relationships

                    ==================================================
                    TOOL SELECTION
                    ==================================================

                    Math
                    → calculator

                    Private documents
                    → rag_search

                    General web information
                    → duckduckgo_search

                    Travel planning
                    → travel_planner

                    PostgreSQL READ / SELECT
                    → postgres_search

                    PostgreSQL INSERT / UPDATE / DELETE
                    → postgres_write

                    ==================================================
                    UPDATE EXAMPLE
                    ==================================================

                    User:

                    Change Customer David country to UAE

                    You should call:

                    postgres_write

                    with:

                    UPDATE customers
                    SET country = 'UAE'
                    WHERE name = 'David';

                    ==================================================
                    INSERT EXAMPLE
                    ==================================================

                    User:

                    Add a new customer John from Dubai

                    You should call:

                    postgres_write

                    with an INSERT query using the
                    customers table and its schema.

                    ==================================================
                    DELETE EXAMPLE
                    ==================================================

                    User:
                    Delete customer David

                    You should call:

                    postgres_write

                    with:

                    DELETE FROM customers
                    WHERE name = 'David';

                    Always use a WHERE clause for UPDATE
                    and DELETE operations.
                """
            ), 
        HumanMessage( content=user_input ) ]
# # -------------------------------------------------------- # First LLM call # -------------------------------------------------------- 
    response = model_with_tools.invoke(messages)
 # -------------------------------------------------------- # No tool required # -------------------------------------------------------- 
    if not response.tool_calls: 
        return { "answer": response.content, "tools_used": [] }
# -------------------------------------------------------- # Add AI response # -------------------------------------------------------- 
    messages.append(response) 
    tools_used = [] 
# -------------------------------------------------------- # Execute tools # -------------------------------------------------------- 
    for tool_call in response.tool_calls: 
        tool_name = tool_call["name"] 
        tool_args = tool_call["args"] 
        tools_used.append( { "name": tool_name, "args": tool_args } )
        # Find tool 
        selected_tool = tools_by_name.get( tool_name ) 
        if selected_tool is None: 
            result = ( f"Tool '{tool_name}' was not found." ) 
        else: 
            try: 
                result = selected_tool.invoke( tool_args ) 
            except Exception as e: 
                result = ( f"Tool execution failed: {str(e)}" )
            # Convert result to string 
            if isinstance( result, (dict, list) ): 
                result_content = json.dumps( result ) 
            else:
                result_content = str(result)
            # Add result to conversation 
            messages.append( ToolMessage( content=result_content, tool_call_id=tool_call["id"] ) ) 
            # Save result for UI 
            tools_used[-1]["result"] = result 
            # -------------------------------------------------------- # Final LLM call # -------------------------------------------------------- 
    final_response = model_with_tools.invoke( messages ) 
    return { "answer": final_response.content, "tools_used": tools_used }