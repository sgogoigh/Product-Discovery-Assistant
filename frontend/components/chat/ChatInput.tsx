"use client";

import { useState } from "react";

export default function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled?: boolean;
}) {
  const [text, setText] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text.trim());
    setText("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t bg-white p-3 flex gap-2"
    >
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask for a product…"
        className="
          flex-1
          rounded-md
          border
          border-gray-300
          px-3
          py-2
          text-sm
          text-gray-900
          placeholder-gray-400
          bg-white
          focus:outline-none
          focus:ring-2
          focus:ring-blue-500
          focus:border-blue-500
        "
      />

      <button
        type="submit"
        disabled={disabled}
        className="
          rounded-md
          bg-blue-600
          px-4
          py-2
          text-sm
          font-medium
          text-white
          hover:bg-blue-700
          disabled:opacity-50
        "
      >
        Send
      </button>
    </form>
  );
}