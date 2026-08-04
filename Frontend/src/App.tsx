import React, { useState } from "react";
import { usePRStream } from "./hooks/usePRStream";
import { apiService } from "./services/api";
import { RiskGauge } from "./components/RiskGauge";
import { FindingsAccordion } from "./components/FindingsAccordion";
import { HITLActionBar } from "./components/HITLActionBar";
import {
  Shield,
  Radio,
  Play,
  RefreshCw,
  Terminal,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

export default function App() {
  const [inputThreadId, setInputThreadId] =
    useState<string>("pr-owner-repo-101");
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulationMsg, setSimulationMsg] = useState<string | null>(null);

  const {
    threadId,
    status,
    riskScore,
    confidence,
    summary,
    findings,
    isPausedForHITL,
    isConnected,
    error,
    connectToStream,
    submitDecision,
  } = usePRStream();

  const handleRunSimulation = async () => {
    setIsSimulating(true);
    setSimulationMsg(null);
    try {
      const response = await apiService.triggerTestReview();
      setInputThreadId(response.thread_id);
      connectToStream(response.thread_id);
      setSimulationMsg(
        `Simulation started! Tracking thread: ${response.thread_id}`,
      );
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      setSimulationMsg(
        err.response?.data?.detail ||
          "Failed to start simulation. Make sure FastAPI is running!",
      );
    } finally {
      setIsSimulating(false);
    }
  };

  const handleManualConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputThreadId.trim()) return;
    connectToStream(inputThreadId.trim());
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-100">
                LangGraph Autonomous DevOps & PR Security Agent
              </h1>
              <p className="text-xs text-slate-400">
                Real-Time HITL & SSE Streaming Dashboard
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Stream Status:</span>
            <div
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
                isConnected
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : "bg-slate-800 text-slate-400 border-slate-700"
              }`}
            >
              <Radio
                className={`w-3.5 h-3.5 ${isConnected ? "animate-pulse text-emerald-400" : ""}`}
              />
              {isConnected ? "LIVE STREAMING" : "DISCONNECTED"}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-6">
        <section className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm shadow-md">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <form
              onSubmit={handleManualConnect}
              className="flex items-center gap-3 flex-1"
            >
              <div className="relative flex-1 max-w-md">
                <Terminal className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={inputThreadId}
                  onChange={(e) => setInputThreadId(e.target.value)}
                  placeholder="Enter thread ID (e.g., pr-owner-repo-101)..."
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                />
              </div>
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-medium text-sm transition-all cursor-pointer"
              >
                Connect Stream
              </button>
            </form>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleRunSimulation}
                disabled={isSimulating}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-all shadow-lg shadow-blue-900/30 disabled:opacity-50 cursor-pointer"
              >
                {isSimulating ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                🚀 Run Simulation PR Review
              </button>
            </div>
          </div>

          {simulationMsg && (
            <div className="mt-4 p-3 rounded-xl bg-blue-950/30 border border-blue-500/30 text-xs text-blue-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0" />
              {simulationMsg}
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 rounded-xl bg-red-950/30 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              {error}
            </div>
          )}
        </section>

        {threadId ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column: Risk Gauge (1 Col) */}
            <div className="lg:col-span-1 space-y-6">
              <RiskGauge
                riskScore={riskScore}
                confidence={confidence}
                status={status}
              />

              <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 text-xs space-y-3">
                <span className="font-semibold text-slate-400 uppercase tracking-wider block">
                  Workflow Session Info
                </span>
                <div className="flex justify-between py-1 border-b border-slate-800/80">
                  <span className="text-slate-500">Thread ID</span>
                  <span className="font-mono text-slate-300">{threadId}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/80">
                  <span className="text-slate-500">Current Status</span>
                  <span className="font-semibold text-blue-400">{status}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">HITL Paused</span>
                  <span className="font-semibold text-slate-300">
                    {isPausedForHITL ? "YES (Waiting)" : "NO"}
                  </span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2 space-y-6">
              <HITLActionBar
                isPaused={isPausedForHITL}
                status={status}
                onSubmitDecision={submitDecision}
              />

              {summary && (
                <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
                  <h3 className="text-sm font-semibold text-slate-300">
                    📋 Executive Summary
                  </h3>
                  <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
                    {summary}
                  </p>
                </div>
              )}

              <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40">
                <FindingsAccordion findings={findings} />
              </div>
            </div>
          </div>
        ) : (
          <div className="p-16 rounded-2xl border border-dashed border-slate-800 bg-slate-900/20 text-center">
            <Shield className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-base font-semibold text-slate-400">
              No Pull Request Stream Active
            </h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
              Click{" "}
              <strong className="text-slate-300">
                "🚀 Run Simulation PR Review"
              </strong>{" "}
              above or enter a valid thread ID to start inspecting AI security
              reviews in real time.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
