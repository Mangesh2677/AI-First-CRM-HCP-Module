import React, { useEffect } from "react";
import { useDispatch } from "react-redux";
import "./App.css";
import { loadHCPs } from "./store/hcpSlice";
import LogInteractionScreen from "./components/LogInteractionScreen";

export default function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(loadHCPs());
  }, [dispatch]);

  return (
    <div className="app-shell">
      <div className="topbar">
        <div className="topbar-brand">
          <div className="topbar-mark">HX</div>
          <div>
            <div className="topbar-title">HCP CRM</div>
            <div className="topbar-subtitle">AI-first HCP interaction module</div>
          </div>
        </div>
      </div>
      <LogInteractionScreen />
    </div>
  );
}
