"use client";

import { useEffect, useRef, useState } from "react";

export default function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled?: boolean;
}) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Keep focus in the box between turns.
  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const value = text.trim();
    if (!value || disabled) return;
    onSend(value);
    setText("");
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-100 bg-white p-3">
      <div className="flex items-center gap-2 rounded-full bg-gray-50 p-1.5 pl-4 ring-1 ring-gray-200 transition focus-within:bg-white focus-within:ring-2 focus-within:ring-brand-300">
        <label htmlFor="chat-input" className="sr-only">
          Message Neu
        </label>
        <input
          id="chat-input"
          ref={inputRef}
          type="text"
          value={text}
          maxLength={500}
          autoComplete="off"
          onChange={(e) => setText(e.target.value)}
          placeholder="Tell Neu what you're looking for…"
          className="min-w-0 flex-1 bg-transparent text-sm text-gray-900 placeholder-gray-400 focus:outline-none"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          aria-label="Send"
          className="bg-brand-gradient grid h-9 w-9 shrink-0 place-items-center rounded-full text-white transition hover:brightness-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:opacity-40"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden>
            <path d="M3.4 2.3a.75.75 0 0 0-1 .9l1.8 5.9h6.3a.75.75 0 0 1 0 1.5H4.2l-1.8 5.9a.75.75 0 0 0 1 .9l14.5-7a.75.75 0 0 0 0-1.4L3.4 2.3Z" />
          </svg>
        </button>
      </div>
    </form>
  );
}
