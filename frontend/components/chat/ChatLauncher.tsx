"use client";

export default function ChatLauncher() {
  return (
    <button
      onClick={() => window.open("/chat", "_blank")}
      className="
        fixed bottom-6 right-6
        bg-blue-600 hover:bg-blue-700
        text-white
        w-14 h-14
        rounded-full
        flex items-center justify-center
        shadow-lg
        transition
      "
      aria-label="Open chat"
      title="Chat with assistant"
    >
      💬
    </button>
  );
}