import { configureStore } from "@reduxjs/toolkit";
import hcpsReducer from "./hcpSlice";
import interactionsReducer from "./interactionsSlice";
import chatReducer from "./chatSlice";

export const store = configureStore({
  reducer: {
    hcps: hcpsReducer,
    interactions: interactionsReducer,
    chat: chatReducer,
  },
});
