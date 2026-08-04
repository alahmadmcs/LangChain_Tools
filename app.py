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

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)
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


tools = [calculator, web_search, get_weather, travel_planner, rag_search]

tool_names = [tool.name for tool in tools]
tools_by_name = {tool.name: tool for tool in tools}

model_with_tools = llm.bind_tools(tools)
# ============================================================ # Main function called by Streamlit 

def ask_agent(user_input: str): 
    messages = [ 
        SystemMessage( 
         content="""
                You are a helpful assistant.

                Available tools:

                1. calculator
                Use for mathematical calculations:
                - addition
                - subtraction
                - multiplication
                - division

                2. duckduckgo_search
                Use for general web searches.

                3. travel_planner
                Use for travel planning and current travel information.
                4. get_weather
                Use for getting current weather information.

                5. rag_search
                Use for searching the application's private documents.

                Tool selection rules:

                - Use rag_search for questions about uploaded/private documents.
                - Use travel_planner for travel planning.
                - Use duckduckgo_search for general web searches.
                - Use calculator for mathematical calculations.

                Do not use web search when the answer can be found
                in the private documents.
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