"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
        <Link href="/" className="flex items-center gap-2 text-lg font-extrabold tracking-tight text-gray-900">
          <span className="bg-brand-gradient grid h-8 w-8 place-items-center rounded-xl text-sm text-white shadow-sm" aria-hidden>
            N
          </span>
          Neusearch
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
