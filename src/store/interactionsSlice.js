import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { fetchInteractions, createInteraction, updateInteraction, deleteInteraction } from "../api/api";

export const loadInteractions = createAsyncThunk("interactions/load", async (hcpId) =>
  fetchInteractions(hcpId)
);
export const addInteraction = createAsyncThunk("interactions/add", async (payload) =>
  createInteraction(payload)
);
export const editInteraction = createAsyncThunk("interactions/edit", async ({ id, payload }) =>
  updateInteraction(id, payload)
);
export const removeInteraction = createAsyncThunk("interactions/remove", async (id) => {
  await deleteInteraction(id);
  return id;
});

const interactionsSlice = createSlice({
  name: "interactions",
  initialState: { items: [], status: "idle", error: null },
  reducers: {
    upsertFromAgent(state, action) {
      // allows the chat flow to optimistically prepend a note that the
      // agent logged something, before the list is refreshed from the API
      state.items.unshift(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadInteractions.pending, (state) => {
        state.status = "loading";
      })
      .addCase(loadInteractions.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(addInteraction.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
      })
      .addCase(editInteraction.fulfilled, (state, action) => {
        const idx = state.items.findIndex((i) => i.id === action.payload.id);
        if (idx !== -1) state.items[idx] = action.payload;
      })
      .addCase(removeInteraction.fulfilled, (state, action) => {
        state.items = state.items.filter((i) => i.id !== action.payload);
      });
  },
});

export const { upsertFromAgent } = interactionsSlice.actions;
export default interactionsSlice.reducer;
