const API_URL = "http://localhost:8001";


export async function sendMessage(
    sessionId,
    message
) {

    const response = await fetch(
        `${API_URL}/chat`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
            },

            body: JSON.stringify({
                session_id: sessionId,
                message: message,
            }),
        }
    );


    if (!response.ok) {

        throw new Error(
            "Failed to communicate with AI server"
        );
    }


    return await response.json();
}


export async function sendApproval(
    sessionId,
    approved
) {

    const response = await fetch(
        `${API_URL}/chat/approval`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
            },

            body: JSON.stringify({
                session_id: sessionId,
                approved: approved,
            }),
        }
    );


    if (!response.ok) {

        throw new Error(
            "Failed to submit approval"
        );
    }


    return await response.json();
}