import React from "react";

export default function ApprovalCard({
    approvalRequest,
    onApprove,
    onReject,
    disabled = false,
}) {

    if (!approvalRequest) {
        return null;
    }


    const message =
        approvalRequest.message ||
        "The agent wants to modify the database.";


    const operations =
        approvalRequest.operations || [];


    return (

        <div className="approval-container">

            <div className="approval-card">


                {/* =================================================
                    HEADER
                ================================================= */}

                <div className="approval-title-row">

                    <div className="approval-warning-icon">
                        ⚠
                    </div>

                    <div>

                        <h3>
                            Database approval required
                        </h3>

                        <p>
                            {message}
                        </p>

                    </div>

                </div>


                {/* =================================================
                    OPERATIONS
                ================================================= */}

                {operations.map(
                    (
                        operation,
                        index
                    ) => {

                        const toolName =
                            operation.tool_name ||
                            operation.tool ||
                            "unknown";


                        const args =
                            operation.arguments ||
                            {};


                        return (

                            <div
                                className="approval-operation"
                                key={index}
                            >

                                <div className="operation-header">

                                    <span>
                                        DATABASE OPERATION
                                    </span>

                                    <code>
                                        {toolName}
                                    </code>

                                </div>


                                {args.query && (

                                    <div className="sql-preview">

                                        <div className="sql-label">
                                            SQL QUERY
                                        </div>

                                        <pre>
                                            {args.query}
                                        </pre>

                                    </div>

                                )}


                                {!args.query && (

                                    <pre className="json-preview">

                                        {JSON.stringify(
                                            args,
                                            null,
                                            2
                                        )}

                                    </pre>

                                )}

                            </div>

                        );

                    }
                )}


                {/* =================================================
                    WARNING
                ================================================= */}

                <div className="approval-warning">

                    <span>
                        🔐
                    </span>

                    <div>

                        <strong>
                            Human approval required
                        </strong>

                        <p>
                            The database will not be
                            modified until you approve
                            this operation.
                        </p>

                    </div>

                </div>


                {/* =================================================
                    BUTTONS
                ================================================= */}

                <div className="approval-actions">

                    <button

                        className="reject-button"

                        onClick={
                            onReject
                        }

                        disabled={
                            disabled
                        }

                    >

                        {disabled
                            ? "Processing..."
                            : "✕ Reject"}

                    </button>


                    <button

                        className="approve-button"

                        onClick={
                            onApprove
                        }

                        disabled={
                            disabled
                        }

                    >

                        {disabled
                            ? "Processing..."
                            : "✓ Approve & Execute"}

                    </button>

                </div>

            </div>

        </div>

    );
}