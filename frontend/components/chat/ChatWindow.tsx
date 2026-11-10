"use client";

import { useEffect, useRef, useState } from "react";
import { chat } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import type { ChatContext, ChatProductCard as Product, Constraints } from "@/lib/types";
import Button from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Loading";
import ChatBubble from "./ChatBubble";
import ChatInput from "./ChatInput";
import ChatProductCard from "./ChatProductCard";

type Message =
  | { id: string; role: "user"; text: string }
  | {
      id: string;
      role: "bot";
      text: string;
      products?: Product[];
      suggestions?: string[];
      error?: boolean;
      retry?: string; // the user message to resend
    };

type Saved = { messages: Message[]; context: ChatContext | null; constraints: Constraints | null };

const STORAGE_KEY = "neusearch.chat.v2";

const STARTERS = [
  "Leggings for yoga under ₹2,000",
  "Breathable sports bra",
  "Shorts for running",
  "Matching co-ord sets",
];

const welcome = (): Message => ({
  id: "welcome",
  role: "bot",
  text: "Hi! Tell me what you're shopping for in your own words — the activity, fit, fabric or budget — and I'll find matching activewear. You can then say things like \"cheaper\" or \"only shorts\".",
  suggestions: STARTERS,
});

let counter = 0;
const newId = () => `${Date.now()}-${counter++}`;

function load(): Saved | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Saved) : null;
  } catch {
    return null;
  }
}

function save(data: Saved) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    /* storage full or blocked: the chat still works, it just won't survive a refresh */
  }
}

function filterChips(c: Constraints | null): string[] {
  if (!c) return [];
  const chips: string[] = [];
  if (c.category) chips.push(c.category);
  if (c.min_price != null && c.max_price != null) chips.push(`${formatPrice(c.min_price)}–${formatPrice(c.max_price)}`);
  else if (c.max_price != null) chips.push(`Under ${formatPrice(c.max_price)}`);
  else if (c.min_price != null) chips.push(`Over ${formatPrice(c.min_price)}`);
  return chips;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>(() => [welcome()]);
  const [context, setContext] = useState<ChatContext | null>(null);
  const [constraints, setConstraints] = useState<Constraints | null>(null);
  const [loading, setLoading] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Restore the conversation after a refresh (client only, so SSR markup stays stable).
  useEffect(() => {
    const saved = load();
    if (saved?.messages?.length) {
      setMessages(saved.messages);
      setContext(saved.context);
      setConstraints(saved.constraints);
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) save({ messages, context, constraints });
  }, [hydrated, messages, context, constraints]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function send(query: string) {
    if (loading) return;
    setMessages((prev) => [...prev, { id: newId(), role: "user", text: query }]);
    setLoading(true);
    try {
      const res = await chat(query, context);
      setContext(res.context);
      setConstraints(res.constraints);
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "bot", text: res.message, products: res.results, suggestions: res.suggestions },
      ]);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "bot", error: true, retry: query, text: `${detail} Please try again.` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function retry(query: string, errorId: string) {
    // Drop the failed exchange (user message + error bubble) and resend.
    setMessages((prev) => {
      const i = prev.findIndex((m) => m.id === errorId);
      return i > 0 ? prev.slice(0, i - 1) : prev;
    });
    void send(query);
  }

  function reset() {
    setMessages([welcome()]);
    setContext(null);
    setConstraints(null);
  }

  const lastBotId = [...messages].reverse().find((m) => m.role === "bot")?.id;
  const chips = filterChips(constraints);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-gray-200 bg-white">
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-2">
        <h1 className="text-sm font-semibold text-gray-900">Shopping assistant</h1>
        <Button variant="ghost" className="px-2 py-1 text-xs" onClick={reset} disabled={loading}>
          New chat
        </Button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite" aria-busy={loading}>
        {messages.map((m) => {
          if (m.role === "user") {
            return (
              <ChatBubble key={m.id} role="user">
                {m.text}
              </ChatBubble>
            );
          }
          const isLast = m.id === lastBotId && !loading;
          return (
            <div key={m.id} className="space-y-3">
              <ChatBubble role="bot" tone={m.error ? "error" : "default"}>
                {m.text}
              </ChatBubble>

              {m.error && m.retry && (
                <Button variant="secondary" className="ml-1 px-3 py-1 text-xs" onClick={() => retry(m.retry!, m.id)}>
                  Retry
                </Button>
              )}

              {m.products && m.products.length > 0 && (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                  {m.products.map((p) => (
                    <ChatProductCard key={p.product_id} product={p} />
                  ))}
                </div>
              )}

              {isLast && m.suggestions && m.suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2" aria-label="Suggested replies">
                  {m.suggestions.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => (s === "Start over" ? reset() : send(s))}
                      className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="pl-1">
            <Spinner label="Finding products" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {chips.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-t border-gray-100 px-3 pt-2 text-xs text-gray-600">
          <span>Filters:</span>
          {chips.map((c) => (
            <span key={c} className="rounded-full bg-gray-100 px-2 py-0.5 font-medium text-gray-800">
              {c}
            </span>
          ))}
          <button type="button" onClick={() => send("start over")} disabled={loading} className="text-blue-600 hover:underline disabled:opacity-50">
            Clear
          </button>
        </div>
      )}

      <ChatInput onSend={send} disabled={loading} />
    </div>
  );
}
