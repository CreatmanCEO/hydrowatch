'use client';

import { useState } from "react";

interface Command {
  id: string;
  label: string;
  description: string;
  prompt: string;
  category: "analysis" | "monitoring" | "data" | "report";
}

const COMMANDS: Command[] = [
  { id: "scan-anomalies", label: "Scan for anomalies", description: "Check all visible wells", prompt: "Scan all wells in the current viewport for anomalies. Report any debit decline, TDS spikes, or sensor faults.", category: "analysis" },
  { id: "depression-check", label: "Depression cone analysis", description: "Analyze cones in viewport", prompt: "Analyze depression cones for wells in the current viewport. Are any cones overlapping? Is there evidence of well interference?", category: "analysis" },
  { id: "interference-check", label: "Check well interference", description: "Detect mutual influence", prompt: "Check for well interference in the current viewport. Are any wells close enough to affect each other's drawdown?", category: "analysis" },

  { id: "region-overview", label: "Region overview", description: "Summary statistics", prompt: "Give me a complete overview of the region I'm looking at: total wells, active/inactive, average yield, water quality summary, any concerns.", category: "monitoring" },
  { id: "water-quality", label: "Water quality report", description: "TDS and chemical analysis", prompt: "Generate a water quality report for wells in the viewport. Focus on TDS trends, chloride levels, and pH. Flag any wells exceeding UAE drinking water standards.", category: "monitoring" },
  { id: "well-status", label: "Well status check", description: "Status of all wells", prompt: "Report the operational status of all wells in the viewport. Which are active, inactive, or under maintenance? Any that need attention?", category: "monitoring" },

  { id: "trend-analysis", label: "Trend analysis", description: "Debit and water level trends", prompt: "Analyze debit and water level trends for wells in the viewport over the full observation period. Any declining trends?", category: "data" },
  { id: "compare-clusters", label: "Compare clusters", description: "Cross-cluster comparison", prompt: "Compare the well clusters visible in the viewport. Which cluster has the best/worst water quality? Highest/lowest yields?", category: "data" },

  { id: "daily-report", label: "Generate daily report", description: "Summary report", prompt: "Generate a daily monitoring report for all wells in the viewport. Include: operational status, water quality summary, anomalies detected, and recommendations.", category: "report" },
];

const CATEGORY_LABELS: Record<string, string> = {
  analysis: "Analysis",
  monitoring: "Monitoring",
  data: "Data",
  report: "Reports",
};

interface Props {
  onExecute: (prompt: string) => void;
  disabled: boolean;
}

export function CommandBar({ onExecute, disabled }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative px-4 py-1.5 border-t bg-gray-50/50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-blue-600 transition-colors disabled:opacity-50"
      >
        <span>Quick commands</span>
        <span className={`transition-transform ${isOpen ? "rotate-180" : ""}`}>&#9662;</span>
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-4 right-4 mb-1 bg-white border rounded-lg shadow-lg max-h-[300px] overflow-y-auto z-20">
          {(["analysis", "monitoring", "data", "report"] as const).map(category => (
            <div key={category}>
              <div className="px-3 py-1.5 text-[10px] uppercase font-semibold text-gray-400 bg-gray-50 sticky top-0">
                {CATEGORY_LABELS[category]}
              </div>
              {COMMANDS.filter(c => c.category === category).map(cmd => (
                <button
                  key={cmd.id}
                  onClick={() => { onExecute(cmd.prompt); setIsOpen(false); }}
                  className="w-full flex items-start gap-2 px-3 py-2 hover:bg-blue-50 text-left transition-colors"
                >
                  <div>
                    <div className="text-sm font-medium text-gray-800">{cmd.label}</div>
                    <div className="text-xs text-gray-400">{cmd.description}</div>
                  </div>
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
