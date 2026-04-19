'use client';

import type { ChatMessage } from "@/types";
import { AnomalyCardComponent } from "./AnomalyCard";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? "bg-blue-600 text-white rounded-br-md"
            : "bg-gray-100 text-gray-900 rounded-bl-md"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>

        {/* Render structured cards */}
        {message.cards?.map((card, i) => {
          if (card.type === "anomaly_card") {
            return <AnomalyCardComponent key={i} card={card} />;
          }
          if (card.type === "validation_result") {
            return (
              <div key={i} className="mt-2 p-2 bg-white rounded border text-xs">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`font-bold ${card.valid ? "text-green-600" : "text-red-600"}`}>
                    {card.valid ? "VALID" : "INVALID"}
                  </span>
                  <span className="text-gray-500">
                    {card.valid_rows}/{card.total_rows} rows valid
                  </span>
                </div>
                {card.errors.length > 0 && (
                  <ul className="text-red-600 list-disc list-inside">
                    {card.errors.map((e, j) => <li key={j}>{e}</li>)}
                  </ul>
                )}
                {card.warnings.length > 0 && (
                  <ul className="text-yellow-600 list-disc list-inside">
                    {card.warnings.map((w, j) => <li key={j}>{w}</li>)}
                  </ul>
                )}
              </div>
            );
          }
          if (card.type === "region_stats") {
            return (
              <div key={i} className="mt-2 p-2 bg-white rounded border text-xs">
                <div className="font-medium mb-1">Region: {card.well_count} wells ({card.active_count} active)</div>
                <div className="text-gray-600">Avg debit: {card.avg_debit_ls} L/s &middot; Avg TDS: {card.avg_tds_mgl} mg/L</div>
                {card.anomaly_count > 0 && <div className="text-red-600 mt-1">{card.anomaly_count} anomalies detected</div>}
              </div>
            );
          }
          if (card.type === "well_history") {
            return (
              <div key={i} className="mt-2 p-2 bg-white rounded border text-xs">
                <div className="font-medium">{card.well_id}: {card.parameter}</div>
                <div className="text-gray-600">Trend: {card.trend} &middot; {card.values.length} data points</div>
              </div>
            );
          }
          return null;
        })}

        <span className="text-[10px] opacity-50 mt-1 block">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}
