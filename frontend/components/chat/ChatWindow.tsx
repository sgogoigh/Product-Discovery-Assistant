"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { chat } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import type { ChatContext, ChatProductCard as Product, Constraints } from "@/lib/types";
import ChatBubble, { NeuAvatar, TypingBubble } from "./ChatBubble";
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
  { emoji: "🧘", text: "Leggings for yoga under ₹2,000" },
  { emoji: "🏃", text: "Breathable sports bra for running" },
  { emoji: "☀️", text: "Shorts for hot weather" },
  { emoji: "✨", text: "Matching co-ord sets" },
];

const welcome = (): Message => ({
  id: "welcome",
  role: "bot",
  text: "Hey! I'm Neu, your activewear stylist. Tell me what you're shopping for — the activity, the fit, the fabric or your budget — and I'll pull out the best matches. You can steer me any time with things like \"cheaper\" or \"only shorts\".",
});

let counter = 0;
const newId = () => `${Date.now()}-${counter++}`;

function load(): Saved | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    const saved = raw ? (JSON.parse(raw) as Saved) : null;
    return saved?.messages?.length ? saved : null;
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

function ChatWindowInner() {
  // Rendered on the client only (see the dynamic export), so storage can be read during init.
  const [initial] = useState(load);
  const [messages, setMessages] = useState<Message[]>(() => initial?.messages ?? [welcome()]);
  const [context, setContext] = useState<ChatContext | null>(initial?.context ?? null);
  const [constraints, setConstraints] = useState<Constraints | null>(initial?.constraints ?? null);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    save({ messages, context, constraints });
  }, [messages, context, constraints]);

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
        { id: newId(), role: "bot", error: true, retry: query, text: `Sorry, I hit a snag: ${detail}` },
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
  const fresh = messages.length === 1 && !loading;

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-3xl bg-white shadow-xl shadow-brand-100/60 ring-1 ring-gray-100">
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-3">
          <NeuAvatar className="h-10 w-10 text-sm" />
          <div>
            <h1 className="text-sm font-bold text-gray-900">Neu</h1>
            <p className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="h-2 w-2 rounded-full bg-emerald-400" aria-hidden />
              Your activewear stylist
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={reset}
          disabled={loading || fresh}
          className="rounded-full px-3 py-1.5 text-xs font-semibold text-gray-600 ring-1 ring-gray-200 transition hover:bg-brand-50 hover:text-brand-700 hover:ring-brand-200 disabled:opacity-40"
        >
          ↺ New chat
        </button>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto bg-gradient-to-b from-brand-50/40 to-accent-50/30 px-4 py-5" aria-live="polite" aria-busy={loading}>
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
                <button
                  type="button"
                  onClick={() => retry(m.retry!, m.id)}
                  className="ml-10 rounded-full bg-white px-4 py-1.5 text-xs font-semibold text-red-700 ring-1 ring-red-200 hover:bg-red-50"
                >
                  ↻ Try again
                </button>
              )}

              {m.products && m.products.length > 0 && (
                <div className="grid grid-cols-2 gap-3 sm:ml-10 sm:grid-cols-3 lg:grid-cols-4">
                  {m.products.map((p) => (
                    <ChatProductCard key={p.product_id} product={p} />
                  ))}
                </div>
              )}

              {isLast && m.suggestions && m.suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2 sm:ml-10" aria-label="Suggested replies">
                  {m.suggestions.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => (s === "Start over" ? reset() : send(s))}
                      className="rounded-full bg-white px-3.5 py-1.5 text-xs font-semibold text-brand-700 ring-1 ring-brand-200 transition hover:bg-brand-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {fresh && (
          <div className="grid gap-2 sm:ml-10 sm:grid-cols-2" aria-label="Conversation starters">
            {STARTERS.map((s) => (
              <button
                key={s.text}
                type="button"
                onClick={() => send(s.text)}
                className="flex items-center gap-3 rounded-2xl bg-white p-3 text-left text-sm font-medium text-gray-800 ring-1 ring-gray-100 transition hover:-translate-y-0.5 hover:shadow-md hover:ring-brand-200"
              >
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-lg" aria-hidden>
                  {s.emoji}
                </span>
                {s.text}
              </button>
            ))}
          </div>
        )}

        {loading && <TypingBubble />}
        <div ref={bottomRef} />
      </div>

      {chips.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 border-t border-gray-100 px-4 pt-2.5 text-xs text-gray-500">
          <span>Filters</span>
          {chips.map((c) => (
            <span key={c} className="rounded-full bg-accent-50 px-2.5 py-0.5 font-semibold text-accent-700">
              {c}
            </span>
          ))}
          <button
            type="button"
            onClick={() => send("start over")}
            disabled={loading}
            className="font-semibold text-brand-600 hover:underline disabled:opacity-50"
          >
            Clear
          </button>
        </div>
      )}

      <ChatInput onSend={send} disabled={loading} />
    </div>
  );
}

function ChatSkeleton() {
  return <div className="h-full animate-pulse rounded-3xl bg-white ring-1 ring-gray-100" aria-hidden />;
}

/** Client-only: the conversation lives in sessionStorage, which the server can't see. */
const ChatWindow = dynamic(() => Promise.resolve(ChatWindowInner), { ssr: false, loading: ChatSkeleton });
export default ChatWindow;
