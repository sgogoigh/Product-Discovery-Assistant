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
      aria-label="Chat with Neu, the shopping assistant"
      className="bg-brand-gradient fixed bottom-5 right-5 z-30 flex h-14 items-center gap-2 rounded-full px-5 text-sm font-semibold text-white shadow-xl shadow-brand-200 transition hover:-translate-y-0.5 hover:brightness-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-300 focus-visible:ring-offset-2"
    >
      <span aria-hidden className="text-lg">💬</span>
      <span className="hidden sm:inline">Ask Neu</span>
    </Link>
  );
}
