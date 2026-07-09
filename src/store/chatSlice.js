import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { sendChatMessage } from "../api/api";

export const sendMessage = createAsyncThunk(
  "chat/send",
  async ({ message, sessionId }) => sendChatMessage(message, sessionId)
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    sessionId: `session-${Date.now()}`,
    messages: [
      {
        role: "agent",
        text:
          "Hi, I'm your CRM assistant. Tell me about a visit, call, or email " +
          "you just had \u2014 e.g. \u201cI met Dr. Rao today, discussed Cardiozen, " +
          "she was positive, follow up in 2 weeks.\u201d",
        toolCalls: [],
      },
    ],
    status: "idle",
    error: null,
  },
  reducers: {
    pushUserMessage(state, action) {
      state.messages.push({ role: "user", text: action.payload, toolCalls: [] });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.status = "loading";
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.messages.push({
          role: "agent",
          text: action.payload.reply,
          toolCalls: action.payload.tool_calls || [],
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
        state.messages.push({
          role: "agent",
          text: "Sorry, something went wrong reaching the agent. Please try again.",
          toolCalls: [],
        });
      });
  },
});

export const { pushUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
