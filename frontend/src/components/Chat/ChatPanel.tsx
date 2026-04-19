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
              <div className="text-center text-gray-400 text-sm mt-8">
                <p className="mb-3">Ask about wells, anomalies, or upload CSV data.</p>
                <div className="space-y-2 text-xs">
                  {[
                    "Show anomalies in the viewport",
                    "What is the status of well AUH-01-003?",
                    "Region statistics for visible area",
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInput(suggestion)}
                      className="block mx-auto text-gray-400 hover:text-blue-500 transition-colors cursor-pointer"
                    >
                      &rarr; {suggestion}
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
