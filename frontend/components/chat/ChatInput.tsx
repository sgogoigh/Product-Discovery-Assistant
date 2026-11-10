"use client";

import { useEffect, useRef, useState } from "react";
import Button from "@/components/ui/Button";

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
    <form onSubmit={handleSubmit} className="flex gap-2 border-t border-gray-200 bg-white p-3">
      <label htmlFor="chat-input" className="sr-only">
        Message the shopping assistant
      </label>
      <input
        id="chat-input"
        ref={inputRef}
        type="text"
        value={text}
        maxLength={500}
        autoComplete="off"
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. high-waisted leggings for yoga under ₹2,000"
        className="flex-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <Button type="submit" disabled={disabled || !text.trim()}>
        Send
      </Button>
    </form>
  );
}
