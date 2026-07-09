import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { addInteraction } from "../store/interactionsSlice";
import HCPPicker from "./HCPPicker";

const initialForm = {
  hcp_id: "",
  interaction_type: "visit",
  interaction_date: new Date().toISOString().slice(0, 10),
  raw_notes: "",
  products_discussed: "",
  next_steps: "",
};

export default function InteractionForm() {
  const dispatch = useDispatch();
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);
  const [savedMsg, setSavedMsg] = useState(null);

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.hcp_id || !form.raw_notes.trim()) return;
    setSubmitting(true);
    setSavedMsg(null);
    try {
      const payload = {
        ...form,
        hcp_id: Number(form.hcp_id),
        interaction_date: new Date(form.interaction_date).toISOString(),
      };
      const result = await dispatch(addInteraction(payload)).unwrap();
      setSavedMsg(`Saved \u2014 interaction #${result.id}. AI summary: "${result.summary}"`);
      setForm((f) => ({ ...initialForm, hcp_id: f.hcp_id }));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="form-grid" onSubmit={handleSubmit}>
      <div className="field">
        <label>Healthcare Professional</label>
        <HCPPicker value={form.hcp_id} onChange={(id) => setForm((f) => ({ ...f, hcp_id: id }))} />
      </div>

      <div className="field-row">
        <div className="field">
          <label>Interaction type</label>
          <select value={form.interaction_type} onChange={update("interaction_type")}>
            <option value="visit">In-person visit</option>
            <option value="call">Phone call</option>
            <option value="email">Email</option>
            <option value="conference">Conference / event</option>
          </select>
        </div>
        <div className="field">
          <label>Date</label>
          <input type="date" value={form.interaction_date} onChange={update("interaction_date")} />
        </div>
      </div>

      <div className="field">
        <label>Notes</label>
        <textarea
          placeholder="What happened? e.g. Discussed Cardiozen dosing questions, she wants updated efficacy data before next quarter..."
          value={form.raw_notes}
          onChange={update("raw_notes")}
        />
      </div>

      <div className="ai-note">
        <span className="ai-dot" />
        <span>
          On save, the LangGraph agent's <strong>log_interaction</strong> tool runs your notes
          through the Groq LLM to auto-generate a summary, sentiment, and next steps — you
          can leave the fields below blank and let it fill them in, or set them yourself.
        </span>
      </div>

      <div className="field-row">
        <div className="field">
          <label>Products discussed (optional)</label>
          <input
            placeholder="e.g. Cardiozen, Renolex"
            value={form.products_discussed}
            onChange={update("products_discussed")}
          />
        </div>
        <div className="field">
          <label>Next steps (optional)</label>
          <input
            placeholder="e.g. Send updated efficacy data"
            value={form.next_steps}
            onChange={update("next_steps")}
          />
        </div>
      </div>

      <div>
        <button className="submit-btn" type="submit" disabled={submitting}>
          {submitting ? "Saving\u2026" : "Log Interaction"}
        </button>
      </div>

      {savedMsg && <div className="ai-note">{savedMsg}</div>}
    </form>
  );
}
