import React from "react";

import Chat from "./components/Chat";

import "./App.css";


function App() {

    return (

        <div className="app">

            {/* <header className="app-header">

                <h1>
                    🤖 AI Tools Assistant
                </h1>

                <p>
                    LangGraph + PostgreSQL +
                    SQL Server + RAG + Web Search
                </p>

            </header> */}


            <main>

                <Chat />

            </main>

        </div>

    );
}


export default App;