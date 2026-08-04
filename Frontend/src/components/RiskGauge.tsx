import React from "react";
import {
  ShieldAlert,
  ShieldCheck,
  ShieldAlert as ShieldWarning,
  Activity,
} from "lucide-react";

interface RiskGaugeProps {
  riskScore: number;
  confidence: number;
  status: string;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  riskScore,
  confidence,
  status,
}) => {
  const getRiskStyles = (score: number) => {
    if (score >= 80) {
      return {
        text: "text-red-400",
        border: "border-red-500/30",
        bg: "bg-red-950/20",
        badgeBg: "bg-red-500/10 text-red-400 border-red-500/20",
        icon: <ShieldAlert className="w-6 h-6 text-red-400" />,
        label: "Critical Risk",
      };
    }
    if (score >= 50) {
      return {
        text: "text-amber-400",
        border: "border-amber-500/30",
        bg: "bg-amber-950/20",
        badgeBg: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        icon: <ShieldWarning className="w-6 h-6 text-amber-400" />,
        label: "Moderate Risk (HITL Required)",
      };
    }
    return {
      text: "text-emerald-400",
      border: "border-emerald-500/30",
      bg: "bg-emerald-950/20",
      badgeBg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
      label: "Low Risk",
    };
  };

  const styles = getRiskStyles(riskScore);

  return (
    <div
      className={`p-6 rounded-2xl border ${styles.border} ${styles.bg} backdrop-blur-md transition-all duration-300 shadow-lg`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {styles.icon}
          <div>
            <h3 className="text-sm font-medium text-slate-400">
              Security Assessment
            </h3>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold ${styles.badgeBg}`}
            >
              {styles.label}
            </span>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 block">Workflow Status</span>
          <span className="text-sm font-semibold tracking-wide uppercase text-slate-200">
            {status}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mt-6">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <span className="text-xs font-medium text-slate-400 block mb-1">
            Risk Score
          </span>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold ${styles.text}`}>
              {riskScore}
            </span>
            <span className="text-xs text-slate-500">/ 100</span>
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                riskScore >= 80
                  ? "bg-red-500"
                  : riskScore >= 50
                    ? "bg-amber-500"
                    : "bg-emerald-500"
              }`}
              style={{ width: `${Math.min(100, Math.max(0, riskScore))}%` }}
            />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-400">
              AI Confidence
            </span>
            <Activity className="w-3.5 h-3.5 text-slate-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-blue-400">
              {confidence}%
            </span>
          </div>
          {/* Progress bar */}
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, confidence))}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
