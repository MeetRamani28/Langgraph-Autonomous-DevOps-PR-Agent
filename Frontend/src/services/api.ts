import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export interface SecurityFinding {
  title: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  file_path: string;
  line_number?: number;
  description: string;
  recommendation: string;
}

export interface ReviewStatusResponse {
  thread_id: string;
  status: string;
  risk_score: number;
  confidence: number;
  summary: string;
  findings: SecurityFinding[];
  is_paused_for_hitl: boolean;
  next_scheduled_nodes: string[];
  human_approved?: boolean | null;
}

export interface HITLApprovalRequest {
  approved: boolean;
  reviewer_id: string;
  reviewer_notes?: string;
}

export interface WebhookResponse {
  status: string;
  thread_id: string;
  repo: string;
  pr_number: number;
  message: string;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const apiService = {
  async triggerTestReview(): Promise<WebhookResponse> {
    const response = await apiClient.post<WebhookResponse>("/webhook/test");
    return response.data;
  },

  async getReviewStatus(threadId: string): Promise<ReviewStatusResponse> {
    const response = await apiClient.get<ReviewStatusResponse>(
      `/review/${threadId}/status`,
    );
    return response.data;
  },

  async submitHITLDecision(
    threadId: string,
    decision: HITLApprovalRequest,
  ): Promise<{ thread_id: string; status: string; message: string }> {
    const response = await apiClient.post(
      `/review/${threadId}/decide`,
      decision,
    );
    return response.data;
  },

  getSSEStreamUrl(threadId: string): string {
    return `${API_BASE_URL}/stream/${threadId}`;
  },
};
