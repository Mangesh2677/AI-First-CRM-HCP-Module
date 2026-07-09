import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { sendMessage, pushUserMessage } from "../store/chatSlice";
import { loadInteractions } from "../store/interactionsSlice";

const TOOL_LABELS = {
  log_interaction: "Log Interaction",
  edit_interaction: "Edit Interaction",
  get_hcp_history: "Get HCP History",
  schedule_follow_up: "Schedule Follow-up",
  suggest_talking_points: "Suggest Talking Points",
  check_compliance_flags: "Compliance Check",
};

export default function ChatInterface() {
  const dispatch = useDispatch();
  const { messages, status, sessionId } = useSelector((s) => s.chat);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || status === "loading") return;
    dispatch(pushUserMessage(text));
    setInput("");
    const result = await dispatch(sendMessage({ message: text, sessionId }));
    // If a logging/editing tool ran, refresh the interactions list so the
    // right-hand panel reflects the new/updated record immediately.
    const toolNames = (result.payload?.tool_calls || []).map((t) => t.tool);
    if (toolNames.includes("log_interaction") || toolNames.includes("edit_interaction")) {
      dispatch(loadInteractions());
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`bubble-row ${m.role === "user" ? "user" : "agent"}`}>
            <div>
              <div className={`bubble ${m.role === "user" ? "user" : "agent"}`}>{m.text}</div>
              {m.toolCalls?.length > 0 && (
                <div>
                  {m.toolCalls.map((t, j) => (
                    <span className="tool-chip" key={j} title={t.output}>
                      ⚡ {TOOL_LABELS[t.tool] || t.tool}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {status === "loading" && (
          <div className="bubble-row agent">
            <div className="bubble agent">Thinking…</div>
          </div>
        )}
      </div>
      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          placeholder="Tell the agent about a visit, or ask it to edit one, schedule a follow-up..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="chat-send-btn" type="submit" disabled={status === "loading"}>
          Send
        </button>
      </form>
      <div className="chat-hint">
        Try: "I visited Dr. Mehta today, discussed Renolex, she was receptive, follow up in 2
        weeks" or "Edit interaction 3, we actually also discussed Cardiozen."
      </div>
    </div>
  );
}
