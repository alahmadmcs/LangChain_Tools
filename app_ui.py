
import streamlit as st

from app import ask_agent


# ============================================================
# Page configuration
# ============================================================

st.set_page_config(
    page_title="PG Tools",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# Session state
# ============================================================

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []


# ============================================================
# Header
# ============================================================

st.title("🤖 PG Tools Assistant")

st.caption(
    "Groq + LangChain + Tavily + DuckDuckGo + RAG + PostgreSQL"
)


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.header("🔧 Available Tools")
    
    st.write("📟 Calculator")
    st.write("🔎 DuckDuckGo Web Search")
    st.write("🌐 Tavily Travel Planner")
    st.write("📖 RAG Document Search")
    st.write("🌦️ Weather Information")
    st.write("📦 PostgreSQL Search")
    st.write("💾 PostgreSQL Write")

    st.divider()

    if st.button("🗑️ Clear Chat"):

        st.session_state.chat_history = []

        st.rerun()


# ============================================================
# Display chat history
# ============================================================

for chat in st.session_state.chat_history:

    with st.chat_message("user"):

        st.write(
            chat["question"]
        )


    with st.chat_message("assistant"):

        st.write(
            chat["answer"]
        )


        if chat["tools_used"]:

            with st.expander(
                "🔧 Tools used"
            ):

                for tool in chat["tools_used"]:

                    st.write(
                        f"**Tool:** `{tool['name']}`"
                    )

                    st.write(
                        "**Arguments:**"
                    )

                    st.json(
                        tool["args"]
                    )

                    st.write(
                        "**Result:**"
                    )

                    result = tool["result"]

                    if isinstance(
                        result,
                        (dict, list)
                    ):

                        st.json(result)

                    else:

                        st.write(result)


# ============================================================
# User input
# ============================================================

user_input = st.chat_input(
    "Ask something..."
)


if user_input:

    # --------------------------------------------------------
    # Show user question
    # --------------------------------------------------------

    with st.chat_message("user"):

        st.write(user_input)


    # --------------------------------------------------------
    # Call backend
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            result = ask_agent(
                user_input
            )


        # ----------------------------------------------------
        # Show answer
        # ----------------------------------------------------

        st.write(
            result["answer"]
        )


        # ----------------------------------------------------
        # Show tools
        # ----------------------------------------------------

        if result["tools_used"]:

            with st.expander(
                "🔧 Tools used"
            ):

                for tool in result["tools_used"]:

                    st.write(
                        f"**Tool:** `{tool['name']}`"
                    )

                    st.write(
                        "**Arguments:**"
                    )

                    st.json(
                        tool["args"]
                    )

                    st.write(
                        "**Result:**"
                    )

                    tool_result = tool["result"]


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


    # --------------------------------------------------------
    # Save chat
    # --------------------------------------------------------

    st.session_state.chat_history.append(
        {
            "question": user_input,
            "answer": result["answer"],
            "tools_used": result["tools_used"]
        }
    )

