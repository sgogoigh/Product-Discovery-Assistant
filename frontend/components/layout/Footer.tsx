"use client";

import { usePathname } from "next/navigation";
import BrandMark from "./BrandMark";
import Container from "./Container";

export default function Footer() {
  // The chat page fills the viewport; no footer there.
  if (usePathname().startsWith("/chat")) return null;
  return (
    <footer className="mt-16 border-t border-brand-100 bg-white/60">
      <Container className="flex flex-col items-center justify-between gap-2 py-6 text-xs text-gray-500 sm:flex-row">
        <p className="flex items-center gap-2">
          <BrandMark className="h-5 w-5" />
          AI product discovery demo
        </p>
        <p>Products and images from hunnit.com, used for demonstration.</p>
      </Container>
    </footer>
  );
}
