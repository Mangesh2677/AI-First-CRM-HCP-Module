import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

export const fetchHCPs = () => api.get("/api/hcps/").then((r) => r.data);
export const createHCP = (payload) => api.post("/api/hcps/", payload).then((r) => r.data);

export const fetchInteractions = (hcpId) =>
  api.get("/api/interactions/", { params: hcpId ? { hcp_id: hcpId } : {} }).then((r) => r.data);

export const createInteraction = (payload) =>
  api.post("/api/interactions/", payload).then((r) => r.data);

export const updateInteraction = (id, payload) =>
  api.put(`/api/interactions/${id}`, payload).then((r) => r.data);

export const deleteInteraction = (id) =>
  api.delete(`/api/interactions/${id}`).then((r) => r.data);

export const sendChatMessage = (message, sessionId) =>
  api.post("/api/chat/", { message, session_id: sessionId }).then((r) => r.data);

export const resetChatSession = (sessionId) =>
  api.post("/api/chat/reset", null, { params: { session_id: sessionId } }).then((r) => r.data);
