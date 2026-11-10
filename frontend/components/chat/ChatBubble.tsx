import type { ReactNode } from "react";

type ChatBubbleProps = {
  role: "user" | "bot";
  tone?: "default" | "error";
  children: ReactNode;
};

export function NeuAvatar({ className = "h-8 w-8 text-xs" }: { className?: string }) {
  return (
    <span className={`bg-brand-gradient grid shrink-0 place-items-center rounded-full font-bold text-white ${className}`} aria-hidden>
      N
    </span>
  );
}

export default function ChatBubble({ role, tone = "default", children }: ChatBubbleProps) {
  const isUser = role === "user";
  const colours = isUser
    ? "bg-brand-gradient text-white rounded-br-md shadow-sm"
    : tone === "error"
      ? "bg-red-50 text-red-800 ring-1 ring-red-200 rounded-bl-md"
      : "bg-white text-gray-800 ring-1 ring-gray-100 rounded-bl-md shadow-sm";

  return (
    <div className={`flex w-full items-end gap-2 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && <NeuAvatar />}
      <div className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed sm:max-w-[70%] ${colours}`}>
        <span className="sr-only">{isUser ? "You:" : "Neu:"} </span>
        {children}
      </div>
    </div>
  );
}

export function TypingBubble() {
  return (
    <div className="flex items-end gap-2" role="status">
      <NeuAvatar />
      <div className="flex gap-1 rounded-2xl rounded-bl-md bg-white px-4 py-3.5 shadow-sm ring-1 ring-gray-100">
        <span className="sr-only">Neu is looking…</span>
        <span className="typing-dot h-2 w-2 rounded-full bg-brand-400" aria-hidden />
        <span className="typing-dot h-2 w-2 rounded-full bg-brand-400" aria-hidden />
        <span className="typing-dot h-2 w-2 rounded-full bg-brand-400" aria-hidden />
      </div>
    </div>
  );
}
