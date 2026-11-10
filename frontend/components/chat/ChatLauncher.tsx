"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** Floating shortcut to the assistant. Same tab, so the back button returns to shopping. */
export default function ChatLauncher() {
  const pathname = usePathname();
  if (pathname.startsWith("/chat")) return null;

  return (
    <Link
      href="/chat"
      aria-label="Open shopping assistant"
      title="Ask the shopping assistant"
      className="fixed bottom-6 right-6 z-30 flex h-14 items-center gap-2 rounded-full bg-blue-600 px-5 text-sm font-medium text-white shadow-lg transition hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-300"
    >
      <span aria-hidden>💬</span>
      <span className="hidden sm:inline">Ask the assistant</span>
    </Link>
  );
}
