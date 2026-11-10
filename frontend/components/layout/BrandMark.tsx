import { useId } from "react";

/** The brand mark: a magnifier with a spark inside (same artwork as app/icon.svg). */
export default function BrandMark({ className = "h-9 w-9" }: { className?: string }) {
  const id = useId();
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f45b3c" />
          <stop offset="0.55" stopColor="#f0477a" />
          <stop offset="1" stopColor="#7c5cf5" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill={`url(#${id})`} />
      <circle cx="28" cy="28" r="14" fill="none" stroke="#fff" strokeWidth="5.5" />
      <path d="M38.5 38.5 49 49" stroke="#fff" strokeWidth="7" strokeLinecap="round" />
      <path
        d="M28 19.5c.9 4.6 3.9 7.6 8.5 8.5-4.6.9-7.6 3.9-8.5 8.5-.9-4.6-3.9-7.6-8.5-8.5 4.6-.9 7.6-3.9 8.5-8.5Z"
        fill="#fff"
      />
    </svg>
  );
}
