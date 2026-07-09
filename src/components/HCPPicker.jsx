import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { addHCP } from "../store/hcpSlice";

export default function HCPPicker({ value, onChange }) {
  const dispatch = useDispatch();
  const hcps = useSelector((s) => s.hcps.items);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    const result = await dispatch(addHCP({ name: newName.trim() }));
    if (result.payload?.id) {
      onChange(result.payload.id);
      setNewName("");
      setCreating(false);
    }
  };

  return (
    <div className="hcp-picker">
      <select value={value || ""} onChange={(e) => onChange(Number(e.target.value))}>
        <option value="" disabled>
          Select HCP…
        </option>
        {hcps.map((h) => (
          <option key={h.id} value={h.id}>
            {h.name} {h.specialty ? `\u2014 ${h.specialty}` : ""}
          </option>
        ))}
      </select>
      {!creating ? (
        <button type="button" className="link-btn" onClick={() => setCreating(true)}>
          + New HCP
        </button>
      ) : (
        <form onSubmit={handleCreate} style={{ display: "flex", gap: 6 }}>
          <input
            autoFocus
            placeholder="Dr. name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid var(--line)" }}
          />
          <button type="submit" className="link-btn">
            Save
          </button>
        </form>
      )}
    </div>
  );
}
