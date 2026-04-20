import { DynamicWellsMap } from "@/components/Map/DynamicWellsMap";
import { ChatPanel } from "@/components/Chat/ChatPanel";

export default function Home() {
  return (
    <main className="flex h-screen">
      {/* Map — left 60% (full width on mobile) */}
      <div className="w-full md:w-[60%] h-full">
        <DynamicWellsMap />
      </div>

      {/* Chat — right 40% (bottom drawer on mobile) */}
      <div className="hidden md:flex md:w-[40%] md:min-w-[40%] md:max-w-[40%] h-full border-l shrink-0">
        <ChatPanel />
      </div>

      {/* Mobile: bottom drawer toggle */}
      <MobileChatDrawer />
    </main>
  );
}

function MobileChatDrawer() {
  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-50">
      <details className="bg-white border-t shadow-lg">
        <summary className="px-4 py-3 cursor-pointer text-sm font-medium text-gray-700 flex items-center gap-2">
          <span>HydroWatch AI</span>
          <span className="text-xs text-gray-400">tap to open chat</span>
        </summary>
        <div className="h-[60vh]">
          <ChatPanel />
        </div>
      </details>
    </div>
  );
}
