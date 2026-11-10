"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import BrandMark from "./BrandMark";
import Container from "./Container";

const NAV = [
  { href: "/", label: "Shop" },
  { href: "/chat", label: "Ask Neu" },
];

export default function Header() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-brand-100/70 bg-white/80 backdrop-blur">
      <Container className="flex h-14 items-center justify-between">
        <Link
          href="/"
          aria-label="Home"
          className="rounded-xl transition hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
        >
          <BrandMark className="h-9 w-9 drop-shadow-sm" />
        </Link>
        <nav className="flex gap-1 text-sm">
          {NAV.map(({ href, label }) => {
            const active =
              href === "/" ? pathname === "/" || pathname.startsWith("/products") : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`rounded-full px-4 py-1.5 font-medium transition ${
                  active ? "bg-brand-50 text-brand-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </Container>
    </header>
  );
}
