"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Container from "./Container";

const NAV = [
  { href: "/", label: "Shop" },
  { href: "/chat", label: "Assistant" },
];

export default function Header() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/90 backdrop-blur">
      <Container className="flex h-14 items-center justify-between">
        <Link href="/" className="text-lg font-semibold tracking-tight text-gray-900">
          Neusearch
        </Link>
        <nav className="flex gap-1 text-sm">
          {NAV.map(({ href, label }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`rounded-md px-3 py-1.5 ${active ? "bg-gray-100 font-medium text-gray-900" : "text-gray-600 hover:text-gray-900"}`}
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
