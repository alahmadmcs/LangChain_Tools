from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_graph import (
    ask_agent,
    resume_agent,
)


app = FastAPI(
    title="AI Tools Assistant API"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):

    session_id: str

    message: str


class ApprovalRequest(BaseModel):

    session_id: str

    approved: bool


# ============================================================
# CHAT
# ============================================================

@app.post("/chat")
async def chat(
    request: ChatRequest
):

    result = ask_agent(

        user_input=request.message,

        session_id=request.session_id,
    )

    if result.get(
        "requires_approval",
        False
    ):

        return {

            "status":
                "approval_required",

            "session_id":
                request.session_id,

            "answer":
                result.get(
                    "answer",
                    ""
                ),

            "approval_request":
                result.get(
                    "approval_request"
                ),

        }

    return {

        "status":
            "completed",

        "session_id":
            request.session_id,

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


# ============================================================
# APPROVAL
# ============================================================

@app.post("/chat/approval")
async def approval(
    request: ApprovalRequest
):

    result = resume_agent(

        session_id=request.session_id,

        approved=request.approved,
    )

    if result.get(
        "requires_approval",
        False
    ):

        return {

            "status":
                "approval_required",

            "session_id":
                request.session_id,

            "answer":
                result.get(
                    "answer",
                    ""
                ),

            "approval_request":
                result.get(
                    "approval_request"
                ),

        }

    return {

        "status":
            "completed",

        "session_id":
            request.session_id,

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