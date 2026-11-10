export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-gray-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" aria-hidden />
      {label}…
    </span>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4" aria-hidden>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-3">
          <div className="mb-3 aspect-[4/5] rounded bg-gray-200" />
          <div className="mb-2 h-4 w-3/4 rounded bg-gray-200" />
          <div className="h-4 w-1/3 rounded bg-gray-200" />
        </div>
      ))}
    </div>
  );
}
