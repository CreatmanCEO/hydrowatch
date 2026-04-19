'use client';

import { create } from "zustand";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import type { ChatMessage, StructuredCard, SSEEvent, MapContext } from "@/types";

interface ChatState {
  messages: ChatMessage[];
  streamingText: string;
  isLoading: boolean;
  abortController: AbortController | null;

  // Actions
  sendMessage: (text: string, mapContext: MapContext) => Promise<void>;
  cancelStream: () => void;
  clearMessages: () => void;
}

let messageCounter = 0;

function nextId(): string {
  return `msg-${++messageCounter}-${Date.now()}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  streamingText: "",
  isLoading: false,
  abortController: null,

  sendMessage: async (text, mapContext) => {
    const userMsg: ChatMessage = {
      id: nextId(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    set((s) => ({
      messages: [...s.messages, userMsg],
      streamingText: "",
      isLoading: true,
    }));

    const ctrl = new AbortController();
    set({ abortController: ctrl });

    let assistantContent = "";
    const cards: StructuredCard[] = [];

    try {
      await fetchEventSource("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          map_context: mapContext,
        }),
        signal: ctrl.signal,

        onmessage(ev) {
          if (ev.data === "[DONE]") return;

          try {
            const event: SSEEvent = JSON.parse(ev.data);

            switch (event.type) {
              case "token":
                assistantContent += event.content;
                set({ streamingText: assistantContent });
                break;

              case "tool_result":
                if (event.result && typeof event.result === "object") {
                  const result = event.result as Record<string, unknown>;
                  if (result.type === "anomaly_card" || result.type === "validation_result" ||
                      result.type === "region_stats" || result.type === "well_history") {
                    cards.push(result as unknown as StructuredCard);
                  } else if (Array.isArray(event.result)) {
                    for (const item of event.result as Record<string, unknown>[]) {
                      if (item.type) cards.push(item as unknown as StructuredCard);
                    }
                  }
                }
                break;

              case "error":
                assistantContent += `\n\n**Error:** ${event.message}`;
                set({ streamingText: assistantContent });
                break;

              case "done":
                break;
            }
          } catch {
            // ignore parse errors
          }
        },

        onclose() {
          const assistantMsg: ChatMessage = {
            id: nextId(),
            role: "assistant",
            content: assistantContent,
            cards: cards.length > 0 ? cards : undefined,
            timestamp: new Date(),
          };

          set((s) => ({
            messages: [...s.messages, assistantMsg],
            streamingText: "",
            isLoading: false,
            abortController: null,
          }));
        },

        onerror(err) {
          set({ isLoading: false, abortController: null });
          throw err;
        },
      });
    } catch (err) {
      if ((err as Error).name === "AbortError") return;

      const errorMsg: ChatMessage = {
        id: nextId(),
        role: "assistant",
        content: `Connection error: ${(err as Error).message}`,
        timestamp: new Date(),
      };

      set((s) => ({
        messages: [...s.messages, errorMsg],
        streamingText: "",
        isLoading: false,
        abortController: null,
      }));
    }
  },

  cancelStream: () => {
    const ctrl = get().abortController;
    if (ctrl) ctrl.abort();
    set({ isLoading: false, abortController: null, streamingText: "" });
  },

  clearMessages: () => set({ messages: [], streamingText: "" }),
}));
