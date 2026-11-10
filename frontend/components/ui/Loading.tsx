import type { ReactNode } from "react";

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-gray-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-100 border-t-brand-500" aria-hidden />
      {label}…
    </span>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4" aria-hidden>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="animate-pulse rounded-2xl bg-white p-2 ring-1 ring-gray-100">
          <div className="mb-3 aspect-[4/5] rounded-xl bg-brand-50" />
          <div className="mx-1 mb-2 h-4 w-3/4 rounded bg-gray-100" />
          <div className="mx-1 mb-2 h-4 w-1/3 rounded bg-gray-100" />
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="mx-auto max-w-md rounded-2xl bg-white px-6 py-10 text-center ring-1 ring-gray-100">
      <p className="mb-1 text-base font-semibold text-gray-900">{title}</p>
      {children && <div className="text-sm text-gray-500">{children}</div>}
    </div>
  );
}
