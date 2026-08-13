# ============================================================
# app_ui.py
# ============================================================

import uuid
import streamlit as st

from agent_graph import (
    ask_agent,
    resume_agent,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Tools Assistant",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# SESSION ID
# ============================================================

if "session_id" not in st.session_state:

    st.session_state.session_id = str(
        uuid.uuid4()
    )


# ============================================================
# CHAT HISTORY
# ============================================================

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []


# ============================================================
# PENDING APPROVAL
# ============================================================

if "approval_request" not in st.session_state:

    st.session_state.approval_request = None


# ============================================================
# PAGE HEADER
# ============================================================

st.title(
    "🤖 AI Tools Assistant"
)

st.caption(
    "LangGraph + PostgreSQL Memory + "
    "PostgreSQL + SQL Server + RAG + Web Search"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "🔧 Available Tools"
    )

    st.write(
        "🧮 Calculator"
    )

    st.write(
        "🌐 Web Search"
    )

    st.write(
        "🌤️ Weather"
    )

    st.write(
        "✈️ Travel Planner"
    )

    st.write(
        "📖 RAG Document Search"
    )

    st.write(
        "🐘 PostgreSQL Search"
    )

    st.write(
        "✏️ PostgreSQL Write"
    )

    st.write(
        "🗄️ SQL Server Search"
    )

    st.write(
        "✏️ SQL Server Write"
    )

    st.divider()

    st.write(
        "Session ID:"
    )

    st.code(
        st.session_state.session_id
    )

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):

        # ----------------------------------------------------
        # Generate new conversation/thread
        # ----------------------------------------------------

        st.session_state.session_id = str(
            uuid.uuid4()
        )

        # ----------------------------------------------------
        # Clear Streamlit chat
        # ----------------------------------------------------

        st.session_state.chat_history = []

        # ----------------------------------------------------
        # Clear pending approval
        # ----------------------------------------------------

        st.session_state.approval_request = None

        st.rerun()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for index, chat in enumerate(
    st.session_state.chat_history
):

    # ========================================================
    # USER MESSAGE
    # ========================================================

    with st.chat_message(
        "user"
    ):

        st.write(
            chat.get(
                "question",
                ""
            )
        )

    # ========================================================
    # ASSISTANT MESSAGE
    # ========================================================

    with st.chat_message(
        "assistant"
    ):

        st.write(
            chat.get(
                "answer",
                ""
            )
        )

        # ====================================================
        # TOOLS USED
        # ====================================================

        tools_used = chat.get(
            "tools_used",
            []
        )

        if tools_used:

            with st.expander(
                "🔧 Tools used"
            ):

                for tool_index, tool in enumerate(
                    tools_used
                ):

                    st.write(
                        f"### {tool_index + 1}. "
                        f"`{tool.get('name', 'unknown')}`"
                    )

                    # ----------------------------------------
                    # ARGUMENTS
                    # ----------------------------------------

                    st.write(
                        "**Arguments:**"
                    )

                    arguments = tool.get(
                        "args",
                        {}
                    )

                    if isinstance(
                        arguments,
                        (dict, list)
                    ):

                        st.json(
                            arguments
                        )

                    else:

                        st.write(
                            arguments
                        )

                    # ----------------------------------------
                    # RESULT
                    # ----------------------------------------

                    if "result" in tool:

                        st.write(
                            "**Result:**"
                        )

                        tool_result = tool.get(
                            "result"
                        )

                        if isinstance(
                            tool_result,
                            (dict, list)
                        ):

                            st.json(
                                tool_result
                            )

                        else:

                            st.write(
                                tool_result
                            )

                    st.divider()


# ============================================================
# PENDING HUMAN APPROVAL
# ============================================================

if st.session_state.approval_request:

    approval_request = (
        st.session_state.approval_request
    )

    st.warning(
        "⚠️ Human approval required"
    )

    # ========================================================
    # APPROVAL MESSAGE
    # ========================================================

    if isinstance(
        approval_request,
        dict
    ):

        approval_message = (
            approval_request.get(
                "message",
                "The agent wants to modify database data."
            )
        )

    else:

        approval_message = str(
            approval_request
        )

    st.write(
        approval_message
    )

    # ========================================================
    # DISPLAY REQUESTED OPERATIONS
    # ========================================================

    if isinstance(
        approval_request,
        dict
    ):

        operations = (
            approval_request.get(
                "operations",
                []
            )
        )

        if operations:

            st.write(
                "### Requested operation"
            )

            for operation in operations:

                if not isinstance(
                    operation,
                    dict
                ):

                    st.write(
                        operation
                    )

                    continue

                # IMPORTANT:
                # approval_node uses "tool_name"
                tool_name = operation.get(
                    "tool_name",
                    "unknown"
                )

                arguments = operation.get(
                    "arguments",
                    {}
                )

                st.write(
                    f"**Tool:** `{tool_name}`"
                )

                st.write(
                    "**Arguments:**"
                )

                if isinstance(
                    arguments,
                    (dict, list)
                ):

                    st.json(
                        arguments
                    )

                else:

                    st.write(
                        arguments
                    )

    st.divider()

    # ========================================================
    # APPROVE / REJECT BUTTONS
    # ========================================================

    col1, col2 = st.columns(
        2
    )

    # ========================================================
    # APPROVE
    # ========================================================

    with col1:

        approve_clicked = st.button(
            "✅ Approve",
            type="primary",
            use_container_width=True,
            key="approve_database_write",
        )

    # ========================================================
    # REJECT
    # ========================================================

    with col2:

        reject_clicked = st.button(
            "❌ Reject",
            use_container_width=True,
            key="reject_database_write",
        )

    # ========================================================
    # APPROVE ACTION
    # ========================================================

    if approve_clicked:

        with st.spinner(
            "Executing approved database operation..."
        ):

            result = resume_agent(

                session_id=
                    st.session_state.session_id,

                approved=True,
            )

        # ----------------------------------------------------
        # CHECK RESULT
        # ----------------------------------------------------

        if result.get(
            "requires_approval",
            False
        ):

            st.session_state.approval_request = (
                result.get(
                    "approval_request"
                )
            )

        else:

            st.session_state.approval_request = None

        # ----------------------------------------------------
        # ADD RESPONSE TO CHAT
        # ----------------------------------------------------

        st.session_state.chat_history.append(
            {

                "question":
                    "Database write approval",

                "answer":
                    result.get(
                        "answer",
                        ""
                    ),

                "tools_used":
                    result.get(
                        "tools_used",
                        []
                    ),
            }
        )

        st.rerun()

    # ========================================================
    # REJECT ACTION
    # ========================================================

    if reject_clicked:

        with st.spinner(
            "Rejecting database operation..."
        ):

            result = resume_agent(

                session_id=
                    st.session_state.session_id,

                approved=False,
            )

        # ----------------------------------------------------
        # CHECK RESULT
        # ----------------------------------------------------

        if result.get(
            "requires_approval",
            False
        ):

            st.session_state.approval_request = (
                result.get(
                    "approval_request"
                )
            )

        else:

            st.session_state.approval_request = None

        # ----------------------------------------------------
        # ADD RESPONSE TO CHAT
        # ----------------------------------------------------

        st.session_state.chat_history.append(
            {

                "question":
                    "Database write approval",

                "answer":
                    result.get(
                        "answer",
                        ""
                    ),

                "tools_used":
                    result.get(
                        "tools_used",
                        []
                    ),
            }
        )

        st.rerun()
# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask something..."
)


# ============================================================
# PROCESS USER MESSAGE
# ============================================================

if user_input:

    # ========================================================
    # DISPLAY USER MESSAGE
    # ========================================================

    with st.chat_message(
        "user"
    ):

        st.write(
            user_input
        )

    # ========================================================
    # CALL LANGGRAPH
    # ========================================================

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Thinking..."
        ):

            result = ask_agent(
                user_input=user_input,
                session_id=st.session_state.session_id,
            )

        # ====================================================
        # ANSWER
        # ====================================================

        answer = result.get(
            "answer",
            ""
        )

        st.write(
            answer
        )

        # ====================================================
        # TOOLS USED
        # ====================================================

        tools_used = result.get(
            "tools_used",
            []
        )

        if tools_used:

            with st.expander(
                "🔧 Tools used"
            ):

                for tool_index, tool in enumerate(
                    tools_used
                ):

                    st.write(
                        f"### {tool_index + 1}. "
                        f"`{tool.get('name', 'unknown')}`"
                    )

                    st.write(
                        "**Arguments:**"
                    )

                    arguments = tool.get(
                        "args",
                        {}
                    )

                    if isinstance(
                        arguments,
                        (dict, list)
                    ):

                        st.json(
                            arguments
                        )

                    else:

                        st.write(
                            arguments
                        )

                    if "result" in tool:

                        st.write(
                            "**Result:**"
                        )

                        tool_result = tool.get(
                            "result"
                        )

                        if isinstance(
                            tool_result,
                            (dict, list)
                        ):

                            st.json(
                                tool_result
                            )

                        else:

                            st.write(
                                tool_result
                            )

    # ========================================================
    # CHECK APPROVAL
    # ========================================================

    if result.get("requires_approval", False):

        approval_request = result.get(
            "approval_request"
        )

        print("APPROVAL REQUEST FROM AGENT:")
        print(approval_request)

        if approval_request:

            st.session_state.approval_request = (
                approval_request
            )
    # ========================================================
    # SAVE CHAT
    # ========================================================

    st.session_state.chat_history.append(
        {
            "question":
                user_input,

            "answer":
                answer,

            "tools_used":
                tools_used,
        }
    )

    # ========================================================
    # RERUN
    # ========================================================

    st.rerun()