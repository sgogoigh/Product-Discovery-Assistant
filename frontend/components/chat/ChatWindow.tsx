"use client";

import { useEffect, useRef, useState } from "react";
import { chat } from "@/lib/api";
import type { ChatProductCard as Product } from "@/lib/types";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import ChatProductCard from "./ChatProductCard";

type Message =
  | {
      role: "user";
      content: string;
    }
  | {
      role: "bot";
      products?: Product[];
      clarification?: string;
      empty?: boolean;
    };

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [context, setContext] = useState<Record<string, any> | null>(null);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(query: string) {
    setMessages((prev) => [
      ...prev,
      { role: "user", content: query },
    ]);

    setLoading(true);

    try {
      const res = await chat(query, context ?? undefined);
      setContext(res.context ?? null);

      if (res.clarification) {
        setMessages((prev) => [
          ...prev,
          { role: "bot", clarification: res.clarification },
        ]);
        setContext(res.context ?? null);
        return;
      }

      if (!res.results || res.results.length === 0) {
        setMessages((prev) => [
          ...prev,
          { role: "bot", empty: true },
        ]);
        setContext(res.context ?? null);
        return;
      }

      setMessages((prev) => [
        ...prev,
        { role: "bot", products: res.results },
      ]);

      setContext(res.context ?? null);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", empty: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full border rounded-xl bg-white">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {messages.map((m, i) => {
          // User message
          if (m.role === "user") {
            return (
              <ChatBubble
                key={`user-${i}`}
                role="user"
                text={m.content}
              />
            );
          }

          // Empty / welcome state
          if (m.empty) {
            return (
              <ChatBubble
                key={`empty-${i}`}
                role="bot"
                text="Tell me what you’re shopping for — for example: gym wear under ₹2,000."
              />
            );
          }

          return (
            <div key={`bot-${i}`} className="space-y-3">
              {m.clarification && (
                <ChatBubble
                  role="bot"
                  text={m.clarification}
                />
              )}

              {Array.isArray(m.products) && m.products.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {m.products.map((p) => (
                    <ChatProductCard
                      key={p.product_id}
                      product={p}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <ChatBubble role="bot" text="Thinking…" />
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}