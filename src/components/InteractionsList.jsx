import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { loadInteractions, editInteraction, removeInteraction } from "../store/interactionsSlice";

export default function InteractionsList() {
  const dispatch = useDispatch();
  const items = useSelector((s) => s.interactions.items);
  const hcps = useSelector((s) => s.hcps.items);
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    dispatch(loadInteractions());
  }, [dispatch]);

  const hcpName = (id) => hcps.find((h) => h.id === id)?.name || `HCP #${id}`;

  const startEdit = (item) => {
    setEditingId(item.id);
    setEditText(item.next_steps || "");
  };

  const saveEdit = async (id) => {
    await dispatch(editInteraction({ id, payload: { next_steps: editText } }));
    setEditingId(null);
  };

  return (
    <div>
      {items.length === 0 && (
        <div className="empty-state">No interactions logged yet. Use the form or chat to add one.</div>
      )}
      {items.slice(0, 8).map((item) => (
        <div className="interaction-item" key={item.id}>
          <div className="interaction-item-head">
            <span className="interaction-hcp">{hcpName(item.hcp_id)}</span>
            <span className={`sentiment-badge sentiment-${item.sentiment || "neutral"}`}>
              {item.sentiment || "neutral"}
            </span>
          </div>
          <div className="interaction-meta">
            #{item.id} · {item.interaction_type} · {new Date(item.interaction_date).toLocaleDateString()}
          </div>
          <div className="interaction-summary">{item.summary || item.raw_notes}</div>
          {item.products_discussed && (
            <div className="interaction-meta">Products: {item.products_discussed}</div>
          )}

          {editingId === item.id ? (
            <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
              <input
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                placeholder="Next steps"
                style={{ flex: 1, padding: "6px 8px", borderRadius: 6, border: "1px solid var(--line)" }}
              />
              <button className="link-btn" onClick={() => saveEdit(item.id)}>
                Save
              </button>
              <button className="link-btn" onClick={() => setEditingId(null)}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="interaction-actions">
              <button className="link-btn" onClick={() => startEdit(item)}>
                Edit
              </button>
              <button className="link-btn danger" onClick={() => dispatch(removeInteraction(item.id))}>
                Delete
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
