'use client';

import { useState, useRef, useEffect } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useMapStore } from "@/stores/mapStore";
import { MessageBubble } from "./MessageBubble";
import { CSVUpload } from "./CSVUpload";

export function ChatPanel() {
  const [input, setInput] = useState("");
  const [showUpload, setShowUpload] = useState(false);
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
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <div>
          <h2 className="font-semibold text-sm">HydroWatch AI</h2>
          <p className="text-xs text-gray-500">Groundwater monitoring assistant</p>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="text-xs px-3 py-1.5 rounded-md border hover:bg-gray-100 transition-colors"
          title="Upload CSV"
        >
          CSV
        </button>
      </div>

      {/* CSV Upload panel */}
      {showUpload && (
        <div className="border-b">
          <CSVUpload />
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
        {messages.length === 0 && !streamingText && (
          <div className="text-center text-gray-400 text-sm mt-8">
            <p className="mb-2">Ask about wells, anomalies, or upload CSV data.</p>
            <div className="space-y-1 text-xs">
              <p className="text-gray-300">Try: &quot;Show anomalies in the viewport&quot;</p>
              <p className="text-gray-300">Try: &quot;What is the status of well AUH-01-003?&quot;</p>
              <p className="text-gray-300">Try: &quot;Region statistics for visible area&quot;</p>
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

      {/* Input */}
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
