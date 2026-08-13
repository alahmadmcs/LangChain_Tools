# ============================================================
# agent_graph.py
# ============================================================

import os
import json
from langgraph.types import interrupt, Command
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

from langgraph.types import (
    interrupt,
    Command,
)

from graph_state import AgentState

from langgraph_checkpointer import (
    get_checkpointer,
)

from postgres_tool import (
    get_schema_text as get_postgres_schema_text,
)

from sqlserver_tool import (
    get_schema_text as get_sqlserver_schema_text,
)

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


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# LLM
# ============================================================

# llm = ChatOllama(
#     model="mistral:latest",
#     base_url="http://localhost:11434",
#     temperature=0,
# )

llm = ChatOpenAI(
    model="openai/gpt-oss-120b",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv(
        "OPENROUTER_API_KEY"
    ),
    temperature=0,
    max_tokens=4096,
)

# llm = ChatGoogleGenerativeAI(
#     model="gemini-3.6-flash",
#     google_api_key=os.getenv("GOOGLE_API_KEY"),
#     temperature=0,
# )

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

    get_weather,

    travel_planner,

    web_search,

    rag_search,

    postgres_search,

    postgres_write,

    sqlserver_search,

    sqlserver_write,
]


# ============================================================
# TOOL MAP
# ============================================================

tools_by_name = {
    tool.name: tool
    for tool in tools
}


# ============================================================
# LLM WITH TOOLS
# ============================================================

model_with_tools = llm.bind_tools(
    tools
)


# ============================================================
# WRITE TOOLS
# ============================================================

WRITE_TOOLS = {

    "postgres_write",

    "sqlserver_write",

}

def extract_text(content):
    """
    Normalize Gemini/OpenRouter/LangChain content
    into a plain string for the React frontend.
    """

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        result = []

        for block in content:
            if isinstance(block, str):
                result.append(block)

            elif isinstance(block, dict):
                text = block.get("text")

                if isinstance(text, str):
                    result.append(text)

        return "".join(result)

    return str(content)

# ============================================================
# NORMALIZE APPROVAL DECISION
# ============================================================

def normalize_approval_decision(decision):
    """
    Converts different approval responses into:

        approve
        reject

    Supported:

        approve
        approved
        confirm
        confirmed
        yes
        proceed
        True
        {"approved": True}
        {"decision": "approve"}

    """

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(decision, dict):

        if "approved" in decision:

            value = decision["approved"]

            if value is True:
                return "approve"

            if value is False:
                return "reject"

        if "decision" in decision:

            return normalize_approval_decision(
                decision["decision"]
            )

        if "action" in decision:

            return normalize_approval_decision(
                decision["action"]
            )

    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    if decision is True:
        return "approve"

    if decision is False:
        return "reject"

    # --------------------------------------------------------
    # String
    # --------------------------------------------------------

    if isinstance(decision, str):

        value = decision.lower().strip()

        if value in {
            "approve",
            "approved",
            "confirm",
            "confirmed",
            "yes",
            "proceed",
            "allow",
            "accept",
        }:
            return "approve"

        if value in {
            "reject",
            "rejected",
            "deny",
            "denied",
            "no",
            "cancel",
            "decline",
        }:
            return "reject"

    return None


# ============================================================
# SYSTEM MESSAGE
# ============================================================

def build_system_message(
    postgres_schema: str,
    sqlserver_schema: str,
):

    return SystemMessage(

        content=f"""

You are a helpful AI assistant with access to
multiple specialized tools.


==================================================
AVAILABLE TOOLS
==================================================

calculator

get_weather

web_search

travel_planner

rag_search

postgres_search

postgres_write

sqlserver_search

sqlserver_write


==================================================
TOOL SELECTION
==================================================

Math
→ calculator

Weather
→ get_weather

General web information
→ web_search

Travel planning
→ travel_planner

Private documents
→ rag_search

PostgreSQL READ / SELECT
→ postgres_search

PostgreSQL INSERT / UPDATE / DELETE
→ postgres_write

SQL Server READ / SELECT
→ sqlserver_search

SQL Server INSERT / UPDATE / DELETE
→ sqlserver_write


==================================================
POSTGRESQL DATABASE SCHEMA
==================================================

{postgres_schema}


==================================================
SQL SERVER DATABASE SCHEMA
==================================================

{sqlserver_schema}


==================================================
DATABASE RULES
==================================================

1. Never guess table names.

2. Never guess column names.

3. Always use the provided database schema.

4. Use database-specific SQL syntax.

5. Use JOINs when information exists across
   multiple tables.

6. Use aliases for readability.

7. Never use SELECT * for normal user-facing
   database queries.

8. Explicitly select only the columns required
   to answer the user's question.


==================================================
READ / SEARCH
==================================================

PostgreSQL READ
→ postgres_search

SQL Server READ
→ sqlserver_search

Search tools MUST ONLY execute SELECT queries.


==================================================
WRITE / MODIFY
==================================================

PostgreSQL WRITE
→ postgres_write

SQL Server WRITE
→ sqlserver_write

Write tools may execute only:

INSERT
UPDATE
DELETE

Only use write tools when the user explicitly
requests a database modification.


==================================================
WRITE SAFETY
==================================================

Every UPDATE MUST contain a WHERE clause.

Every DELETE MUST contain a WHERE clause.

Never execute:

DROP
ALTER
TRUNCATE
CREATE
GRANT
REVOKE


==================================================
HUMAN APPROVAL
==================================================

PostgreSQL and SQL Server write operations
require human approval.

Before executing:

INSERT
UPDATE
DELETE

using postgres_write or sqlserver_write,
the system will pause and ask the user for
approval.

Never assume approval.

Never execute a write operation without
explicit human approval.


==================================================
INTERNAL ID RULE
==================================================

Internal IDs are technical database identifiers.

IDs may be used internally for:

JOIN
WHERE
UPDATE
DELETE

Do NOT return internal IDs to the user unless
the user explicitly asks for them.


==================================================
JOIN RULE
==================================================

When multiple tables are required:

1. Check the provided schema.

2. Identify the correct tables.

3. Identify the actual relationships.

4. Use JOINs.

5. Use IDs internally when required.

6. Do not return JOIN IDs unless explicitly
   requested.


==================================================
ERROR HANDLING
==================================================

If a tool returns an error:

1. Do not claim that the operation succeeded.

2. Explain the error clearly.

3. If the query can be safely corrected using
   the schema, correct it.

4. Never invent missing data.


==================================================
FINAL RESPONSE
==================================================

Use the tool result as the source of truth.

Do not expose internal IDs unless explicitly
requested.

Do not expose unnecessary SQL or internal
implementation details.

Never claim that a database modification
succeeded unless the write tool confirms it.

"""
    )

def approval_node(state: AgentState):

    messages = state.get("messages", [])

    if not messages:
        return {}

    last_message = messages[-1]

    tool_calls = getattr(
        last_message,
        "tool_calls",
        []
    )

    write_calls = []

    for tool_call in tool_calls:

        tool_name = tool_call.get("name")

        if tool_name in WRITE_TOOLS:
            write_calls.append(tool_call)

    if not write_calls:
        return {}

    operations = []

    for tool_call in write_calls:

        operations.append({
            "tool_name": tool_call.get("name"),
            "arguments": tool_call.get("args", {}),
            "tool_call_id": tool_call.get("id"),
        })

    approval_request = {

        "type": "database_write_approval",

        "message":
            "The agent wants to modify the database. "
            "Do you approve this operation?",

        "operations": operations,
    }

    print()
    print("==========================================")
    print("⏸️ HUMAN APPROVAL REQUIRED")
    print("==========================================")

    print(
        json.dumps(
            approval_request,
            indent=2,
            default=str
        )
    )

    # IMPORTANT:
    # Graph pauses here.
    decision = interrupt(approval_request)

    print()
    print("▶️ HUMAN DECISION:")
    print(decision)

    normalized_decision = normalize_approval_decision(
        decision
    )

    print(
        "▶️ NORMALIZED DECISION:",
        normalized_decision
    )

    # ========================================================
    # APPROVED
    # ========================================================

    if normalized_decision == "approve":

        print(
            "✅ Database modification APPROVED"
        )

        # Continue to tools node.
        return Command(
            goto="tools"
        )

    # ========================================================
    # REJECTED
    # ========================================================

    if normalized_decision == "reject":

        print(
            "❌ Database modification REJECTED"
        )

        rejection_messages = []

        for tool_call in write_calls:

            rejection_messages.append(

                ToolMessage(

                    content=(
                        "The user rejected the requested "
                        "database modification. "
                        "The database was NOT changed."
                    ),

                    tool_call_id=tool_call.get("id"),

                    name=tool_call.get("name"),
                )
            )

        # IMPORTANT:
        # Do NOT go to tools.
        # Go back to agent so it can explain rejection.

        return Command(

            goto="agent",

            update={
                "messages": rejection_messages
            }
        )

    # ========================================================
    # INVALID
    # ========================================================

    print(
        "❌ Invalid approval decision"
    )

    rejection_messages = []

    for tool_call in write_calls:

        rejection_messages.append(

            ToolMessage(

                content=(
                    "The database modification was not "
                    "approved because the approval response "
                    "was invalid. The database was NOT changed."
                ),

                tool_call_id=tool_call.get("id"),

                name=tool_call.get("name"),
            )
        )

    return Command(

        goto="agent",

        update={
            "messages": rejection_messages
        }
    )
# ============================================================
# CREATE GRAPH
# ============================================================

def create_agent_graph(
    model_with_tools,
    tools,
    postgres_schema,
    sqlserver_schema,
    checkpointer,
):

    system_message = build_system_message(
        postgres_schema,
        sqlserver_schema,
    )


    # ========================================================
    # TOOL NODE
    # ========================================================

    tool_node = ToolNode(
        tools
    )


    # ========================================================
    # AGENT NODE
    # ========================================================

    def agent_node(
        state: AgentState
    ):

        messages = state["messages"]


        # ----------------------------------------------------
        # Add system message
        # ----------------------------------------------------

        if not messages:

            messages = [
                system_message
            ]

        elif not isinstance(
            messages[0],
            SystemMessage
        ):

            messages = [
                system_message,
                *messages,
            ]


        # ----------------------------------------------------
        # CALL LLM
        # ----------------------------------------------------

        response = model_with_tools.invoke(
            messages
        )


        print()
        print(
            "=========================================="
        )
        print(
            "🤖 AGENT"
        )
        print(
            "=========================================="
        )

        print(
            response.content
        )


        if response.tool_calls:

            print(
                "Tool calls:"
            )

            for call in response.tool_calls:

                print(
                    call
                )


        return {

            "messages": [
                response
            ]

        }

    
    # ========================================================
    # AGENT → TOOL OR END
    # ========================================================

    def route_after_agent(
        state: AgentState
    ):

        messages = state.get("messages", [])

        if not messages:
            return "end"

        last_message = messages[-1]

        tool_calls = getattr(
            last_message,
            "tool_calls",
            []
        )

        if not tool_calls:
            return "end"

        for tool_call in tool_calls:

            tool_name = tool_call.get("name")

            if tool_name in WRITE_TOOLS:
                return "approval"

        return "tools"

    # ========================================================
    # TOOLS NODE
    # ========================================================

    def tools_node(
        state: AgentState
    ):

        last_message = state[
            "messages"
        ][-1]


        tool_calls = getattr(
            last_message,
            "tool_calls",
            []
        )


        tools_used = []


        # ----------------------------------------------------
        # Log tool calls
        # ----------------------------------------------------

        for tool_call in tool_calls:

            tool_name = tool_call.get(
                "name"
            )

            tool_args = tool_call.get(
                "args",
                {}
            )


            print()
            print(
                "🔧 Tool:",
                tool_name
            )

            print(
                "Arguments:",
                tool_args
            )


            tools_used.append({

                "name":
                    tool_name,

                "args":
                    tool_args,

            })


        # ----------------------------------------------------
        # Execute
        # ----------------------------------------------------

        try:

            result = tool_node.invoke(
                state
            )

        except Exception as e:

            error = (
                "Tool execution failed: "
                f"{str(e)}"
            )

            print(
                "❌",
                error
            )


            return {

                "messages": [
                    ToolMessage(
                        content=error,
                        tool_call_id=(
                            tool_calls[0].get(
                                "id"
                            )
                            if tool_calls
                            else "unknown"
                        ),
                    )
                ],

                "tools_used": [

                    {

                        "name":
                            "unknown",

                        "args": {},

                        "result":
                            error,

                    }

                ],

            }


        # ----------------------------------------------------
        # Extract tool messages
        # ----------------------------------------------------

        tool_messages = result.get(
            "messages",
            []
        )


        # ----------------------------------------------------
        # Attach results
        # ----------------------------------------------------

        for tool_message in tool_messages:

            tool_name = getattr(
                tool_message,
                "name",
                None
            )


            content = (
                tool_message.content
            )


            parsed_result = content


            if isinstance(
                content,
                str
            ):

                try:

                    parsed_result = json.loads(
                        content
                    )

                except Exception:

                    parsed_result = content


            # ------------------------------------------------
            # Match tool call
            # ------------------------------------------------

            for tool_info in tools_used:

                if (
                    tool_info["name"]
                    == tool_name
                ):

                    tool_info[
                        "result"
                    ] = parsed_result

                    break


        return {

            "messages":
                tool_messages,

            "tools_used":
                tools_used,

        }


    # ========================================================
    # GRAPH
    # ========================================================

    workflow = StateGraph(
        AgentState
    )


    # ========================================================
    # NODES
    # ========================================================

    workflow.add_node("agent", agent_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("tools", tools_node)

    workflow.add_edge(START, "agent")

    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "approval": "approval",
            "tools": "tools",
            "end": END,
        },
    )

    workflow.add_edge("tools", "agent")
  


    # ========================================================
    # COMPILE
    # ========================================================

    return workflow.compile(
        checkpointer=checkpointer
    )


# ============================================================
# CHECKPOINTER
# ============================================================

checkpointer = get_checkpointer()


# ============================================================
# CREATE GRAPH ONCE
# ============================================================
#
# IMPORTANT:
#
# Do NOT create the graph inside ask_agent().
#
# The graph is created once when this module is loaded.
#
# ============================================================

graph = create_agent_graph(

    model_with_tools=
        model_with_tools,

    tools=
        tools,

    postgres_schema=
        postgres_schema,

    sqlserver_schema=
        sqlserver_schema,

    checkpointer=
        checkpointer,

)


print(
    "✅ LangGraph initialized"
)


# ============================================================
# ASK AGENT
# ============================================================
def ask_agent(
    user_input: str,
    session_id: str,
):
    """
    Start a new LangGraph execution.

    If a database write requires approval,
    return the interrupt payload to Streamlit.
    """

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    try:

        # ====================================================
        # VALIDATE USER INPUT
        # ====================================================

        if not user_input:
            return {
                "answer": "",
                "tools_used": [],
                "requires_approval": False,
                "approval_request": None,
                "error": False,
            }

        # ====================================================
        # INITIAL STATE
        # ====================================================

        initial_state = {
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ],
            "tools_used": [],
        }

        # ====================================================
        # RUN GRAPH
        # ====================================================

        result = graph.invoke(
            initial_state,
            config=config,
        )

        # ====================================================
        # CHECK INTERRUPT
        # ====================================================

        interrupts = result.get(
            "__interrupt__",
            []
        )

        if interrupts:

            first_interrupt = interrupts[0]

            if hasattr(
                first_interrupt,
                "value"
            ):
                interrupt_value = (
                    first_interrupt.value
                )
            else:
                interrupt_value = (
                    first_interrupt
                )

            print()
            print(
                "=========================================="
            )
            print(
                "⏸️ GRAPH PAUSED FOR HUMAN APPROVAL"
            )
            print(
                "=========================================="
            )

            print(
                json.dumps(
                    interrupt_value,
                    indent=2,
                    default=str
                )
            )

            return {

                "answer":
                    "Database modification requires approval.",

                "tools_used":
                    result.get(
                        "tools_used",
                        []
                    ),

                # IMPORTANT:
                # These names match Streamlit.
                "requires_approval":
                    True,

                "approval_request":
                    interrupt_value,

                "error":
                    False,
            }

        # ====================================================
        # GET MESSAGES
        # ====================================================

        messages = result.get(
            "messages",
            []
        )

        # ====================================================
        # FIND FINAL AI RESPONSE
        # ====================================================

        final_response = None

        for message in reversed(messages):

            if isinstance(
                message,
                AIMessage
            ):

                if not getattr(
                    message,
                    "tool_calls",
                    []
                ):

                    final_response = message

                    break

        # ====================================================
        # NO FINAL RESPONSE
        # ====================================================

        if final_response is None:

            return {

                "answer":
                    "The agent did not produce "
                    "a final response.",

                "tools_used":
                    result.get(
                        "tools_used",
                        []
                    ),

                "requires_approval":
                    False,

                "approval_request":
                    None,

                "error":
                    True,
            }

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "answer":
               # extract_text(final_response.content),
               final_response.content,

            "tools_used":
                result.get(
                    "tools_used",
                    []
                ),

            "requires_approval":
                False,

            "approval_request":
                None,

            "error":
                False,
        }

    except Exception as e:

        print()
        print(
            "❌ Agent Error:"
        )

        print(
            str(e)
        )

        return {

            "answer":
                f"Agent Error: {str(e)}",

            "tools_used":
                [],

            "requires_approval":
                False,

            "approval_request":
                None,

            "error":
                True,
        }
# ============================================================
# RESUME AGENT
# ============================================================
def resume_agent(
    session_id: str,
    approved: bool,
):
    """
    Resume a paused LangGraph execution.

    approved=True
        -> execute pending database write

    approved=False
        -> reject pending database write
    """

    config = {
        "configurable": {
            "thread_id": session_id
        }
    }

    try:

        # ====================================================
        # DECISION
        # ====================================================

        if approved:

            resume_value = "approve"

        else:

            resume_value = "reject"

        print()
        print(
            "=========================================="
        )
        print(
            "▶️ RESUMING LANGGRAPH"
        )
        print(
            "=========================================="
        )

        print(
            "Session ID:",
            session_id
        )

        print(
            "Decision:",
            resume_value
        )

        # ====================================================
        # RESUME INTERRUPTED GRAPH
        # ====================================================

        result = graph.invoke(

            Command(
                resume=resume_value
            ),

            config=config

        )

        # ====================================================
        # CHECK INTERRUPT
        # ====================================================

        interrupts = result.get(
            "__interrupt__",
            []
        )

        if interrupts:

            first_interrupt = interrupts[0]

            if hasattr(
                first_interrupt,
                "value"
            ):

                interrupt_value = (
                    first_interrupt.value
                )

            else:

                interrupt_value = (
                    first_interrupt
                )

            print()
            print(
                "⏸️ ANOTHER APPROVAL REQUIRED"
            )

            return {

                "answer":
                    "Another approval is required.",

                "tools_used":
                    result.get(
                        "tools_used",
                        []
                    ),

                "requires_approval":
                    True,

                "approval_request":
                    interrupt_value,

                "error":
                    False,
            }

        # ====================================================
        # GET MESSAGES
        # ====================================================

        messages = result.get(
            "messages",
            []
        )

        # ====================================================
        # FIND FINAL RESPONSE
        # ====================================================

        final_response = None

        for message in reversed(messages):

            if isinstance(
                message,
                AIMessage
            ):

                if not getattr(
                    message,
                    "tool_calls",
                    []
                ):

                    final_response = message

                    break

        # ====================================================t
        # FINAL RESPONSE
        # ====================================================

        return {

            "answer":

                (
                    final_response.content
                    if final_response
                    else
                    "The operation has completed."
                ),

            "tools_used":
                result.get(
                    "tools_used",
                    []
                ),

            "requires_approval":
                False,

            "approval_request":
                None,

            "error":
                False,
        }

    except Exception as e:

        print()
        print(
            "❌ Resume Agent Error:"
        )

        print(
            str(e)
        )

        return {

            "answer":
                f"Agent Error: {str(e)}",

            "tools_used":
                [],

            "requires_approval":
                False,

            "approval_request":
                None,

            "error":
                True,
        }
   