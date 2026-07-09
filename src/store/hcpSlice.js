import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { fetchHCPs, createHCP } from "../api/api";

export const loadHCPs = createAsyncThunk("hcps/load", async () => fetchHCPs());
export const addHCP = createAsyncThunk("hcps/add", async (payload) => createHCP(payload));

const hcpSlice = createSlice({
  name: "hcps",
  initialState: { items: [], status: "idle", error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(loadHCPs.pending, (state) => {
        state.status = "loading";
      })
      .addCase(loadHCPs.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(loadHCPs.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message;
      })
      .addCase(addHCP.fulfilled, (state, action) => {
        state.items.push(action.payload);
      });
  },
});

export default hcpSlice.reducer;
