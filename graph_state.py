# ============================================================
# graph_state.py
# ============================================================

from typing import (
    Annotated,
    Optional,
)

from typing_extensions import TypedDict

from langchain_core.messages import (
    BaseMessage,
)

from langgraph.graph.message import (
    add_messages,
)


class AgentState(
    TypedDict,
    total=False
):

    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]

    tools_used: list

    approval_status: Optional[str]