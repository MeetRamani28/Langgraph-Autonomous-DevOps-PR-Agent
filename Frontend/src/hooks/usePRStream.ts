import { useState, useEffect, useCallback } from "react";
import { apiService, type SecurityFinding } from "../services/api";

export interface PRStreamState {
  threadId: string | null;
  status: string;
  riskScore: number;
  confidence: number;
  summary: string;
  findings: SecurityFinding[];
  isPausedForHITL: boolean;
  isConnected: boolean;
  error: string | null;
}

export function usePRStream(initialThreadId: string | null = null) {
  const [threadId, setThreadId] = useState<string | null>(initialThreadId);
  const [state, setState] = useState<PRStreamState>({
    threadId: initialThreadId,
    status: "IDLE",
    riskScore: 0,
    confidence: 0,
    summary: "",
    findings: [],
    isPausedForHITL: false,
    isConnected: false,
    error: null,
  });

  const connectToStream = useCallback((targetThreadId: string) => {
    setThreadId(targetThreadId);
    setState((prev) => ({
      ...prev,
      threadId: targetThreadId,
      status: "CONNECTING",
      error: null,
      isConnected: false,
    }));
  }, []);

  useEffect(() => {
    if (!threadId) return;

    const streamUrl = apiService.getSSEStreamUrl(threadId);
    const eventSource = new EventSource(streamUrl);

    const parsePayload = (event: MessageEvent) => {
      try {
        return JSON.parse(event.data);
      } catch (err) {
        console.error("Failed to parse SSE payload:", err);
        return null;
      }
    };

    eventSource.addEventListener("connected", () => {
      setState((prev) => ({
        ...prev,
        isConnected: true,
        status: "ANALYZING",
        error: null,
      }));
    });

    eventSource.addEventListener("state_update", (event: MessageEvent) => {
      const data = parsePayload(event);
      if (!data) return;

      setState((prev) => ({
        ...prev,
        status: data.status || prev.status,
        riskScore: data.risk_score ?? prev.riskScore,
        confidence: data.confidence ?? prev.confidence,
        summary: data.summary || prev.summary,
        findings: data.findings || prev.findings,
        isPausedForHITL: Boolean(data.is_paused_for_hitl),
      }));
    });

    eventSource.addEventListener("hitl_interrupt", (event: MessageEvent) => {
      const data = parsePayload(event);
      if (!data) return;

      setState((prev) => ({
        ...prev,
        status: "AWAITING_APPROVAL",
        riskScore: data.risk_score ?? prev.riskScore,
        confidence: data.confidence ?? prev.confidence,
        summary: data.summary || prev.summary,
        findings: data.findings || prev.findings,
        isPausedForHITL: true,
      }));
    });

    eventSource.addEventListener("completed", (event: MessageEvent) => {
      const data = parsePayload(event);
      setState((prev) => ({
        ...prev,
        status: data?.final_status || "COMPLETED",
        isPausedForHITL: false,
      }));
      eventSource.close();
    });

    eventSource.addEventListener("error", () => {
      setState((prev) => ({
        ...prev,
        isConnected: false,
        error: "SSE stream disconnected or encountered a network error.",
      }));
      eventSource.close();
    });

    return () => {
      eventSource.close();
      setState((prev) => ({ ...prev, isConnected: false }));
    };
  }, [threadId]);

  const submitDecision = async (approved: boolean, notes?: string) => {
    if (!threadId) return;
    try {
      setState((prev) => ({ ...prev, status: "SUBMITTING_DECISION" }));
      await apiService.submitHITLDecision(threadId, {
        approved,
        reviewer_id: "Senior-DevOps-Architect",
        reviewer_notes: notes || (approved ? "Approved via HITL Dashboard." : "Rejected via HITL Dashboard."),
      });
      setState((prev) => ({
        ...prev,
        isPausedForHITL: false,
        status: approved ? "APPROVED" : "REJECTED",
      }));
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        error: err.response?.data?.detail || "Failed to submit HITL decision.",
      }));
    }
  };

  return {
    ...state,
    connectToStream,
    submitDecision,
  };
}