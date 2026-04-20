'use client';

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useMapStore } from "@/stores/mapStore";
import { MessageBubble } from "./MessageBubble";
import { CSVUpload } from "./CSVUpload";
import { MetricsPanel } from "@/components/Metrics/MetricsPanel";

type ViewMode = "chat" | "csv" | "metrics";

export function ChatPanel() {
  const [input, setInput] = useState("");
  const [view, setView] = useState<ViewMode>("chat");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, streamingText, isLoading, sendMessage, cancelStream } = useChatStore();
  const getApiContext = useMapStore((s) => s.getApiContext);

  // Auto-scroll on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const context = getApiContext();
    sendMessage(input.trim(), context);
    setInput("");
    setView("chat");
  };

  const toggleView = (target: ViewMode) => {
    setView((prev) => (prev === target ? "chat" : target));
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <div>
          <h2 className="font-semibold text-sm">HydroWatch AI</h2>
          <p className="text-xs text-gray-500">Groundwater monitoring assistant</p>
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={() => toggleView("csv")}
            className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
              view === "csv" ? "bg-blue-50 border-blue-300 text-blue-700" : "hover:bg-gray-100"
            }`}
          >
            CSV
          </button>
          <button
            onClick={() => toggleView("metrics")}
            className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${
              view === "metrics" ? "bg-purple-50 border-purple-300 text-purple-700" : "hover:bg-gray-100"
            }`}
          >
            Metrics
          </button>
        </div>
      </div>

      {/* View switcher */}
      {view === "csv" && (
        <div className="flex-1 overflow-y-auto border-b">
          <CSVUpload />
        </div>
      )}

      {view === "metrics" && (
        <div className="flex-1 overflow-y-auto">
          <MetricsPanel />
        </div>
      )}

      {view === "chat" && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
            {messages.length === 0 && !streamingText && (
              <div className="px-2 py-4">
                {/* Welcome message styled as assistant bubble */}
                <div className="flex justify-start mb-4">
                  <div className="max-w-[92%] bg-gray-100 text-gray-900 rounded-2xl rounded-bl-md px-4 py-3">
                    <p className="text-sm font-medium mb-2">Welcome to HydroWatch AI</p>
                    <p className="text-sm text-gray-600 mb-3">
                      I am your groundwater monitoring assistant for the Abu Dhabi aquifer network.
                      I can analyze 25 monitoring wells across 4 clusters in real time.
                    </p>

                    <p className="text-xs font-medium text-gray-500 uppercase mb-2">What I can do:</p>
                    <ul className="text-sm text-gray-600 space-y-1 mb-3">
                      <li>&#x1F4CD; Query wells by location, status, or cluster</li>
                      <li>&#x26A0;&#xFE0F; Detect anomalies: debit decline, TDS spikes, sensor faults</li>
                      <li>&#x1F4C8; Analyze time series trends for any parameter</li>
                      <li>&#x1F4CA; Regional statistics for the current viewport</li>
                      <li>&#x1F4C4; Validate uploaded CSV observation files</li>
                    </ul>

                    <p className="text-xs font-medium text-gray-500 uppercase mb-2">How to use:</p>
                    <ul className="text-xs text-gray-500 space-y-1 mb-3">
                      <li>&bull; Click a well on the map &mdash; I&apos;ll see which one you selected</li>
                      <li>&bull; Pan/zoom the map &mdash; I know your current viewport</li>
                      <li>&bull; Toggle layers (Wells, Depression Cones) in the top-right panel</li>
                      <li>&bull; Upload CSV via the <strong>CSV</strong> button above</li>
                      <li>&bull; View model metrics via the <strong>Metrics</strong> button</li>
                    </ul>
                  </div>
                </div>

                {/* Quick action suggestions */}
                <p className="text-xs text-gray-400 text-center mb-2">Try asking:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {[
                    "Show anomalies in the viewport",
                    "Status of well AUH-01-003",
                    "Region statistics",
                    "Which wells have high TDS?",
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInput(suggestion)}
                      className="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Streaming text */}
            {streamingText && (
              <div className="flex justify-start mb-3">
                <div className="max-w-[85%] bg-gray-100 text-gray-900 rounded-2xl rounded-bl-md px-4 py-2.5">
                  <p className="text-sm whitespace-pre-wrap">
                    {streamingText}
                    <span className="inline-block w-1.5 h-4 bg-blue-500 ml-0.5 animate-pulse" />
                  </p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </>
      )}

      {/* Input — always visible */}
      <form onSubmit={handleSubmit} className="border-t px-4 py-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about wells, anomalies..."
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          {isLoading ? (
            <button
              type="button"
              onClick={cancelStream}
              className="px-4 py-2 rounded-lg bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
