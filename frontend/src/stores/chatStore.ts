'use client';

import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import type { ChatMessage, StructuredCard, SSEEvent, MapContext } from "@/types";

interface ChatState {
  messages: ChatMessage[];
  streamingText: string;
  isLoading: boolean;

  // Actions
  sendMessage: (text: string, mapContext: MapContext) => Promise<void>;
  cancelStream: () => void;
  clearMessages: () => void;
}

let messageCounter = 0;
let activeController: AbortController | null = null;

function nextId(): string {
  return `msg-${++messageCounter}-${Date.now()}`;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set) => ({
      messages: [],
      streamingText: "",
      isLoading: false,

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

        activeController = new AbortController();

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
            signal: activeController.signal,

            onmessage(ev) {
              if (ev.data === "[DONE]") return;

              try {
                const event: SSEEvent = JSON.parse(ev.data);

                switch (event.type) {
                  case "token":
                    // Filter raw tool call markup that some models output as text
                    if (event.content.includes("tool_call_begin") ||
                        event.content.includes("tool_calls_begin") ||
                        event.content.includes("tool_call_end") ||
                        event.content.includes("tool_sep") ||
                        event.content.includes("tool_calls_end")) {
                      break;
                    }
                    assistantContent += event.content;
                    set({ streamingText: assistantContent });
                    break;

                  case "tool_result":
                    if (Array.isArray(event.result)) {
                      for (const item of event.result) {
                        if (item && typeof item === "object" && "type" in item) {
                          cards.push(item as StructuredCard);
                        }
                      }
                    } else if (event.result && typeof event.result === "object" && "type" in (event.result as object)) {
                      cards.push(event.result as StructuredCard);
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
              }));
              activeController = null;
            },

            onerror(err) {
              set({ isLoading: false });
              activeController = null;
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
          }));
          activeController = null;
        }
      },

      cancelStream: () => {
        activeController?.abort();
        activeController = null;
        set({ isLoading: false, streamingText: "" });
      },

      clearMessages: () => set({ messages: [], streamingText: "" }),
    }),
    { name: "ChatStore" }
  )
);
