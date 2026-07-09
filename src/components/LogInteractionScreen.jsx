import React, { useState } from "react";
import InteractionForm from "./InteractionForm";
import ChatInterface from "./ChatInterface";
import InteractionsList from "./InteractionsList";

export default function LogInteractionScreen() {
  const [mode, setMode] = useState("form");

  return (
    <div className="main">
      <div className="screen-header">
        <div>
          <h1>Log Interaction</h1>
          <p>Capture an HCP interaction via a structured form, or describe it conversationally.</p>
        </div>
        <div className="mode-toggle">
          <button className={mode === "form" ? "active" : ""} onClick={() => setMode("form")}>
            Structured Form
          </button>
          <button className={mode === "chat" ? "active" : ""} onClick={() => setMode("chat")}>
            Chat with Agent
          </button>
        </div>
      </div>

      <div className="layout-grid">
        <div className="card">
          <h2>{mode === "form" ? "Interaction details" : "Conversational logging"}</h2>
          {mode === "form" ? <InteractionForm /> : <ChatInterface />}
        </div>

        <div className="card">
          <h2>Recent interactions</h2>
          <InteractionsList />
        </div>
      </div>
    </div>
  );
}
