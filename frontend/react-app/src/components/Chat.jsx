import React, { useState, useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";
import ApprovalCard from "./ApprovalCard";


export default function Chat() {

    // =========================================================
    // SESSION
    // =========================================================

    const [sessionId] = useState(
        () => crypto.randomUUID()
    );

    // =========================================================
    // STATE
    // =========================================================

    const [messages, setMessages] = useState([]);

    const [input, setInput] = useState("");

    const [loading, setLoading] = useState(false);

    const [approvalRequest, setApprovalRequest] =
        useState(null);

    const messagesEndRef = useRef(null);

    const textareaRef = useRef(null);


    // =========================================================
    // AUTO SCROLL
    // =========================================================

    useEffect(() => {

        messagesEndRef.current?.scrollIntoView({
            behavior: "smooth",
        });

    }, [messages, loading, approvalRequest]);


    // =========================================================
    // AUTO RESIZE TEXTAREA
    // =========================================================

    const resizeTextarea = () => {

        const textarea =
            textareaRef.current;

        if (!textarea) {
            return;
        }

        textarea.style.height = "auto";

        textarea.style.height =
            Math.min(
                textarea.scrollHeight,
                180
            ) + "px";
    };


    // =========================================================
    // SEND MESSAGE
    // =========================================================

    const sendMessage = async () => {

        if (!input.trim() || loading) {
            return;
        }

        const question =
            input.trim();

        setInput("");

        if (textareaRef.current) {
            textareaRef.current.style.height =
                "auto";
        }


        // =====================================================
        // USER MESSAGE
        // =====================================================

        setMessages(previous => [

            ...previous,

            {
                role: "user",
                content: question,
            },

        ]);

        setLoading(true);


        try {

            const response =
                await fetch(
                    "http://localhost:8001/chat",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },

                        body: JSON.stringify({

                            message:
                                question,

                            session_id:
                                sessionId,

                        }),

                    }
                );


            const data =
                await response.json();
            console.log("=================================");
            console.log("FULL CHAT RESPONSE:");
            console.log(JSON.stringify(data, null, 2));
            console.log("=================================");

            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}: ${
                        JSON.stringify(data)
                    }`
                );

            }


            // console.log(
            //     "CHAT RESPONSE:",
            //     data
            // );


            // =================================================
            // ASSISTANT RESPONSE
            // =================================================

            if (data.answer) {

                setMessages(previous => [

                    ...previous,

                    {
                        role: "assistant",

                        content:
                            data.answer,

                        tools_used:
                            data.tools_used ||
                            [],
                    },

                ]);

            }


            // =================================================
            // APPROVAL
            // =================================================

           if (data.status === "approval_required" && data.approval_request) 
            {
                console.log("DATABASE APPROVAL REQUIRED");
                console.log("Approval request:",data.approval_request);

                setApprovalRequest(
                    data.approval_data ||
                    data.approval_request
                );
                //  addMessage(
                //     "assistant",
                //     data.answer ||
                //     data.approval_request.message ||
                //     "Database modification requires approval."
                // );

                return;
            }
            else {

                setApprovalRequest(null);

            }

        }
        catch (error) {

            console.error(
                "Chat error:",
                error
            );


            setMessages(previous => [

                ...previous,

                {
                    role: "assistant",

                    content:
                        `Something went wrong: ${error.message}`,

                    error: true,
                },

            ]);

        }
        finally {

            setLoading(false);

        }

    };


    // =========================================================
    // APPROVAL
    // =========================================================

    const handleApproval = async (
        approved
    ) => {

        if (loading) {
            return;
        }

        setLoading(true);


        try {

            const response =
                await fetch(
                    "http://localhost:8001/chat/approval",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",
                        },

                        body: JSON.stringify({

                            session_id:
                                sessionId,

                            approved:
                                approved,

                        }),

                    }
                );


            const data =
                await response.json();
           
            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}: ${
                        JSON.stringify(data)
                    }`
                );

            }


            console.log(
                "APPROVAL RESPONSE:",
                data
            );


            // =================================================
            // ADD RESULT
            // =================================================

            if (data.answer) {

                setMessages(previous => [

                    ...previous,

                    {
                        role: "assistant",

                        content:
                            data.answer,

                        tools_used:
                            data.tools_used ||
                            [],
                    },

                ]);

            }


            // =================================================
            // ANOTHER APPROVAL
            // =================================================

            if (
                data.approval_required === true ||
                data.requires_approval === true
            ) {

                setApprovalRequest(
                    data.approval_data ||
                    data.approval_request
                );

            }
            else {

                setApprovalRequest(null);

            }

        }
        catch (error) {

            console.error(
                "Approval error:",
                error
            );


            setMessages(previous => [

                ...previous,

                {
                    role: "assistant",

                    content:
                        `Approval failed: ${error.message}`,

                    error: true,
                },

            ]);

        }
        finally {

            setLoading(false);

        }

    };


    // =========================================================
    // ENTER KEY
    // =========================================================

    const handleKeyDown = (
        event
    ) => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();

        }

    };


    // =========================================================
    // NEW CHAT
    // =========================================================

    const clearChat = () => {

        setMessages([]);

        setApprovalRequest(null);

        setInput("");

    };


    // =========================================================
    // QUICK PROMPTS
    // =========================================================

    const quickPrompts = [

        "Show 10 employees",

        "Show pending requests",

        "Show today's attendance",

        "Find employees working from home",

    ];


    // =========================================================
    // UI
    // =========================================================

    return (

        <div className="ai-layout">


            {/* =================================================
                SIDEBAR
            ================================================= */}

            <aside className="sidebar">

                <div className="brand">

                    <div className="brand-icon">
                        ✦
                    </div>

                    <div>

                        <div className="brand-title">
                            AI Assistant
                        </div>

                        <div className="brand-subtitle">
                            Agent Workspace
                        </div>

                    </div>

                </div>


                <button
                    className="new-chat-button"
                    onClick={clearChat}
                >

                    <span>
                        ＋
                    </span>

                    New conversation

                </button>


                {/* =================================================
                    TOOLS
                ================================================= */}

                <div className="sidebar-section">

                    <div className="sidebar-heading">
                        AVAILABLE TOOLS
                    </div>


                    <div className="sidebar-tool">
                        <span>🧮</span>
                        Calculator
                    </div>

                    <div className="sidebar-tool">
                        <span>🌐</span>
                        Web Search
                    </div>

                    <div className="sidebar-tool">
                        <span>🌤️</span>
                        Weather
                    </div>

                    <div className="sidebar-tool">
                        <span>✈️</span>
                        Travel Planner
                    </div>

                    <div className="sidebar-tool">
                        <span>📚</span>
                        RAG Search
                    </div>

                    <div className="sidebar-tool">
                        <span>🐘</span>
                        PostgreSQL
                    </div>

                    <div className="sidebar-tool">
                        <span>🗄️</span>
                        SQL Server
                    </div>

                </div>


                {/* =================================================
                    DATABASE STATUS
                ================================================= */}

                <div className="sidebar-section">

                    <div className="sidebar-heading">
                        SYSTEM
                    </div>


                    <div className="system-status">

                        <span className="status-dot"></span>

                        <span>
                            Agent Online
                        </span>

                    </div>


                    <div className="system-status">

                        <span className="status-dot"></span>

                        <span>
                            Database Connected
                        </span>

                    </div>

                </div>


                {/* =================================================
                    SESSION
                ================================================= */}

                <div className="sidebar-bottom">

                    <div className="session-label">
                        SESSION
                    </div>

                    <div className="session-id">
                        {sessionId.substring(0, 18)}...
                    </div>

                </div>

            </aside>


            {/* =================================================
                MAIN
            ================================================= */}

            <main className="main-area">


                {/* =================================================
                    HEADER
                ================================================= */}

                <header className="topbar">

                    <div>
                        <div className="topbar-title">
                         <font size="6">✦</font>  AI Tools Assistant
                        </div>

                        <div className="topbar-subtitle">

                            LangGraph Agent
                            <span>•</span>
                            Human-in-the-loop
                            <span>•</span>
                            Database Tools

                        </div>

                    </div>


                    <div className="topbar-status">

                        <span className="online-dot"></span>

                        Online

                    </div>

                </header>


                {/* =================================================
                    CHAT
                ================================================= */}

                <section className="chat-area">


                    {/* =================================================
                        EMPTY STATE
                    ================================================= */}

                    {messages.length === 0 && (

                        <div className="welcome">

                            <div className="welcome-icon">
                                ✦
                            </div>

                            <h1>
                                How can I help?
                            </h1>

                            <p>
                                Ask me about your data,
                                documents, employees,
                                requests, or anything
                                else supported by your
                                tools.
                            </p>


                            <div className="quick-prompts">

                                {quickPrompts.map(
                                    (prompt) => (

                                        <button
                                            key={prompt}
                                            onClick={() => {
                                                setInput(
                                                    prompt
                                                );

                                                setTimeout(
                                                    resizeTextarea,
                                                    0
                                                );
                                            }}
                                        >

                                            {prompt}

                                        </button>

                                    )
                                )}

                            </div>

                        </div>

                    )}


                    {/* =================================================
                        MESSAGES
                    ================================================= */}

                    <div className="messages-container">

                        {messages.map(
                            (
                                message,
                                index
                            ) => (

                                <ChatMessage
                                    key={index}
                                    message={message}
                                />

                            )
                        )}


                        {/* =================================================
                            LOADING
                        ================================================= */}

                        {loading && (

                            <div className="typing-row">

                                <div className="assistant-avatar">
                                    ✦
                                </div>

                                <div className="typing">

                                    <span></span>
                                    <span></span>
                                    <span></span>

                                </div>

                            </div>

                        )}


                        <div
                            ref={messagesEndRef}
                        />

                    </div>

                </section>


                {/* =================================================
                    APPROVAL
                ================================================= */}

                {approvalRequest && (

                    <ApprovalCard

                        approvalRequest={
                            approvalRequest
                        }

                        onApprove={() =>
                            handleApproval(true)
                        }

                        onReject={() =>
                            handleApproval(false)
                        }

                        disabled={
                            loading
                        }

                    />

                )}


                {/* =================================================
                    INPUT
                ================================================= */}

                <div className="input-wrapper">

                    <div className="input-box">

                        <textarea

                            ref={
                                textareaRef
                            }

                            value={
                                input
                            }

                            onChange={
                                (event) => {

                                    setInput(
                                        event.target.value
                                    );

                                    resizeTextarea();

                                }
                            }

                            onKeyDown={
                                handleKeyDown
                            }

                            placeholder={
                                approvalRequest
                                    ? "Approve or reject the pending operation above..."
                                    : "Ask anything..."
                            }

                            disabled={
                                loading ||
                                approvalRequest !== null
                            }

                            rows={1}

                        />


                        <div className="input-footer">

                            <div className="input-hint">

                                <span>
                                    ↵
                                </span>

                                Send

                                <span>
                                    ⇧ ↵
                                </span>

                                New line

                            </div>


                            <button

                                className="send-button"

                                onClick={
                                    sendMessage
                                }

                                disabled={
                                    loading ||
                                    !input.trim() ||
                                    approvalRequest !== null
                                }

                            >

                                {loading
                                    ? "..."
                                    : "↑"}

                            </button>

                        </div>

                    </div>

                    <div className="privacy-text">

                        AI can make mistakes.
                        Verify important information.

                    </div>

                </div>

            </main>

        </div>

    );
}