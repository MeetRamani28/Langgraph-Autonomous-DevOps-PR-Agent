import React, { useState } from "react";
import { CheckCircle, XCircle, AlertCircle, Loader2 } from "lucide-react";

interface HITLActionBarProps {
  isPaused: boolean;
  status: string;
  onSubmitDecision: (approved: boolean, notes?: string) => Promise<void>;
}

export const HITLActionBar: React.FC<HITLActionBarProps> = ({
  isPaused,
  status,
  onSubmitDecision,
}) => {
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleDecision = async (approved: boolean) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onSubmitDecision(approved, notes);
      setNotes("");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isPaused) {
    if (status === "APPROVED") {
      return (
        <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
          <p className="text-sm text-emerald-300 font-medium">
            Human-In-The-Loop: Pull Request has been APPROVED and resumed.
          </p>
        </div>
      );
    }
    if (status === "REJECTED") {
      return (
        <div className="p-4 rounded-xl border border-red-500/30 bg-red-950/20 flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-400 shrink-0" />
          <p className="text-sm text-red-300 font-medium">
            Human-In-The-Loop: Pull Request has been REJECTED and execution
            stopped.
          </p>
        </div>
      );
    }
    return null;
  }

  return (
    <div className="p-6 rounded-2xl border border-amber-500/40 bg-amber-950/20 backdrop-blur-md shadow-xl space-y-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <h3 className="text-base font-semibold text-amber-300">
            Action Required: Human-In-The-Loop (HITL) Review
          </h3>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">
            LangGraph paused automated execution because the Risk Score exceeded
            safety thresholds or confidence was low. Please review the findings
            below and authorize the PR decision.
          </p>
        </div>
      </div>

      <div>
        <label
          htmlFor="reviewer-notes"
          className="text-xs font-medium text-slate-400 block mb-1.5"
        >
          Reviewer Notes (Optional)
        </label>
        <textarea
          id="reviewer-notes"
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g., Vulnerability confirmed. Fix required before merging."
          disabled={isSubmitting}
          className="w-full rounded-xl bg-slate-900/80 border border-slate-700/80 p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all disabled:opacity-50"
        />
      </div>

      <div className="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          onClick={() => handleDecision(false)}
          disabled={isSubmitting}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-red-500/30 bg-red-600/20 hover:bg-red-600/30 text-red-300 font-medium text-sm transition-all disabled:opacity-50 cursor-pointer"
        >
          {isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <XCircle className="w-4 h-4" />
          )}
          Reject PR
        </button>

        <button
          type="button"
          onClick={() => handleDecision(true)}
          disabled={isSubmitting}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm transition-all shadow-lg shadow-emerald-900/30 disabled:opacity-50 cursor-pointer"
        >
          {isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle className="w-4 h-4" />
          )}
          Approve & Resume Graph
        </button>
      </div>
    </div>
  );
};
