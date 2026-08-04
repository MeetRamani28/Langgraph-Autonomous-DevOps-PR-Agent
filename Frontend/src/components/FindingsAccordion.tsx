import React, { useState } from "react";
import type { SecurityFinding } from "../services/api";
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  FileCode,
  CheckCircle2,
} from "lucide-react";

interface FindingsAccordionProps {
  findings: SecurityFinding[];
}

export const FindingsAccordion: React.FC<FindingsAccordionProps> = ({
  findings,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0); // First item open by default

  const toggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case "CRITICAL":
        return "bg-red-500/10 text-red-400 border-red-500/30";
      case "HIGH":
        return "bg-orange-500/10 text-orange-400 border-orange-500/30";
      case "MEDIUM":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      default:
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
    }
  };

  if (!findings || findings.length === 0) {
    return (
      <div className="p-8 rounded-2xl border border-emerald-500/20 bg-emerald-950/10 text-center">
        <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
        <h4 className="text-base font-semibold text-emerald-300">
          Clean Security Review
        </h4>
        <p className="text-sm text-slate-400 mt-1">
          No critical vulnerabilities or specification violations detected in
          this pull request.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Detected Findings ({findings.length})
        </h3>
      </div>

      {findings.map((finding, idx) => {
        const isExpanded = expandedIndex === idx;

        return (
          <div
            key={idx}
            className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur-sm overflow-hidden transition-all duration-200"
          >
            <button
              onClick={() => toggleExpand(idx)}
              className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-800/40 transition-colors"
            >
              <div className="flex items-center gap-3 pr-4">
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-md border font-semibold tracking-wide uppercase ${getSeverityBadge(
                    finding.severity,
                  )}`}
                >
                  {finding.severity}
                </span>
                <span className="text-sm font-medium text-slate-200">
                  {finding.title}
                </span>
              </div>
              <div className="flex items-center gap-3 text-slate-400">
                <span className="text-xs font-mono bg-slate-800 px-2 py-1 rounded text-slate-300 flex items-center gap-1.5">
                  <FileCode className="w-3.5 h-3.5" />
                  {finding.file_path}
                  {finding.line_number ? ` : Line ~${finding.line_number}` : ""}
                </span>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </div>
            </button>

            {isExpanded && (
              <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 space-y-4 text-sm">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Vulnerability Description
                  </span>
                  <p className="text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800/60">
                    {finding.description}
                  </p>
                </div>

                <div>
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
                    Architectural Recommendation
                  </span>
                  <p className="text-slate-200 leading-relaxed bg-emerald-950/20 border border-emerald-500/20 p-3 rounded-lg">
                    {finding.recommendation}
                  </p>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
