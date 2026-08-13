import React from "react";
import "./ChatMessage.css"; // Import the CSS file for styling
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
function isObjectArray(value) {
    return (
        Array.isArray(value) &&
        value.length > 0 &&
        value.every(
            (item) =>
                item !== null &&
                typeof item === "object" &&
                !Array.isArray(item)
        )
    );
}

function getTableData(result) {
    // Direct array
    if (isObjectArray(result)) {
        return result;
    }

    // { data: [...] }
    if (
        result &&
        typeof result === "object" &&
        isObjectArray(result.data)
    ) {
        return result.data;
    }

    // { rows: [...] }
    if (
        result &&
        typeof result === "object" &&
        isObjectArray(result.rows)
    ) {
        return result.rows;
    }

    // { results: [...] }
    if (
        result &&
        typeof result === "object" &&
        isObjectArray(result.results)
    ) {
        return result.results;
    }

    // JSON string
    if (typeof result === "string") {
        try {
            const parsed = JSON.parse(result);

            if (isObjectArray(parsed)) {
                return parsed;
            }

            if (
                parsed &&
                isObjectArray(parsed.data)
            ) {
                return parsed.data;
            }

            if (
                parsed &&
                isObjectArray(parsed.rows)
            ) {
                return parsed.rows;
            }

            if (
                parsed &&
                isObjectArray(parsed.results)
            ) {
                return parsed.results;
            }

        } catch {
            return null;
        }
    }

    return null;
}


function formatCellValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    if (
        typeof value === "object"
    ) {
        return JSON.stringify(value);
    }

    return String(value);
}


function DataTable({ rows }) {

    if (!rows || rows.length === 0) {
        return null;
    }

    // Collect ALL columns from ALL rows
    const columns = [];

    rows.forEach((row) => {

        Object.keys(row).forEach((key) => {

            if (!columns.includes(key)) {
                columns.push(key);
            }

        });

    });


    return (
        <div className="data-table-container">

            <div className="table-header">

                <span>
                    Query Results
                </span>

                <span className="row-count">
                    {rows.length}{" "}
                    {rows.length === 1
                        ? "record"
                        : "records"}
                </span>

            </div>


            <div className="table-scroll">

                <table className="data-table">

                    <thead>

                        <tr>

                            {columns.map(
                                (column) => (

                                    <th
                                        key={column}
                                    >
                                        {column}
                                    </th>

                                )
                            )}

                        </tr>

                    </thead>


                    <tbody>

                        {rows.map(
                            (row, rowIndex) => (

                                <tr
                                    key={rowIndex}
                                >

                                    {columns.map(
                                        (column) => (

                                            <td
                                                key={
                                                    column
                                                }
                                            >
                                                {formatCellValue(
                                                    row[
                                                        column
                                                    ]
                                                )}
                                            </td>

                                        )
                                    )}

                                </tr>

                            )
                        )}

                    </tbody>

                </table>

            </div>

        </div>
    );
}


export default function ChatMessage({
    message
}) {

    const isUser =
        message.role === "user";


    return (

        <div
            className={
                isUser
                    ? "chat-row user-row"
                    : "chat-row assistant-row"
            }
        >

            <div className="chat-avatar">

                {isUser
                    ? "U"
                    : "AI"}

            </div>


            <div className="chat-content">

                {/* ============================================
                    AI / USER MESSAGE
                ============================================ */}
                 {/* {message.content && (

                    <div className="chat-bubble">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {message.content}
                            </ReactMarkdown>
                    </div>

                )} 
 */}
                {message.content && message.role == "user" && (
                    <div className="chat-bubble">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                        </ReactMarkdown>
                    </div>
                )}

                {/* ============================================
                    TOOL RESULTS
                ============================================ */}

                {message.tools_used &&
                    message.tools_used.length >
                        0 && (

                        <div className="tool-results">

                            {message.tools_used.map(
                                (
                                    tool,
                                    index
                                ) => {

                                    const rows =
                                        getTableData(
                                            tool.result
                                        );
                                    if (rows && rows.length > 0) {
                                        // Rows exist
                       
                                    return (

                                        <div
                                            key={index}
                                        >

                                            {/* SQL RESULT TABLE */}

                                            {rows ? (

                                                <DataTable
                                                    rows={
                                                        rows
                                                    }
                                                />

                                            ) : (

                                                <div className="tool-result-text">

                                                    {typeof tool.result ===
                                                    "object"
                                                        ? JSON.stringify(
                                                              tool.result,
                                                              null,
                                                              2
                                                          )
                                                        : String(
                                                              tool.result ||
                                                                  ""
                                                          )}

                                                </div>

                                            )}

                                        </div>

                                    );
                                    } else {
                                        // No rows
                                        return (
                                               <div className="chat-bubble">
                                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                            {message.content}
                                                        </ReactMarkdown>
                                                </div>
                                        );
                                    }
                                                
                                }
                            )}

                        </div>

                    )}

            </div>

        </div>

    );
}