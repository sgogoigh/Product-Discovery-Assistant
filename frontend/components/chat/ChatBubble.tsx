import type { ReactNode } from "react";

type ChatBubbleProps = {
  role: "user" | "bot";
  tone?: "default" | "error";
  children: ReactNode;
};

export default function ChatBubble({ role, tone = "default", children }: ChatBubbleProps) {
  const isUser = role === "user";
  const colours = isUser
    ? "bg-blue-600 text-white rounded-br-none"
    : tone === "error"
      ? "bg-red-50 text-red-800 border border-red-200 rounded-bl-none"
      : "bg-gray-100 text-gray-900 border border-gray-200 rounded-bl-none";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] whitespace-pre-wrap rounded-xl px-4 py-2 text-sm leading-relaxed sm:max-w-[75%] ${colours}`}>
        <span className="sr-only">{isUser ? "You:" : "Assistant:"} </span>
        {children}
      </div>
    </div>
  );
}
