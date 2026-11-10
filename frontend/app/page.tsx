"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import type { ChatResponse, Product } from "@/lib/types";
import { chat, getProducts } from "@/lib/api";
import ProductGrid from "@/components/product/ProductGrid";
import Container from "@/components/layout/Container";
import Button from "@/components/ui/Button";
import { ProductGridSkeleton } from "@/components/ui/Loading";

type Catalog = { status: "loading" } | { status: "error"; message: string } | { status: "ok"; products: Product[] };
type Search =
  | { status: "idle" }
  | { status: "loading"; query: string }
  | { status: "error"; query: string; message: string }
  | { status: "ok"; query: string; res: ChatResponse };

export default function HomePage() {
  const [catalog, setCatalog] = useState<Catalog>({ status: "loading" });
  const [search, setSearch] = useState<Search>({ status: "idle" });
  const [query, setQuery] = useState("");

  const fetchCatalog = useCallback(() => {
    getProducts()
      .then((products) => setCatalog({ status: "ok", products }))
      .catch((err: Error) => setCatalog({ status: "error", message: err.message }));
  }, []);

  useEffect(fetchCatalog, [fetchCatalog]);

  function retryCatalog() {
    setCatalog({ status: "loading" });
    fetchCatalog();
  }

  async function handleSearch(e?: React.FormEvent) {
    e?.preventDefault();
    const q = query.trim();
    if (!q || search.status === "loading") return;
    setSearch({ status: "loading", query: q });
    try {
      // One-shot search: no conversation context.
      const res = await chat(q, null);
      setSearch({ status: "ok", query: q, res });
    } catch (err) {
      setSearch({ status: "error", query: q, message: err instanceof Error ? err.message : "Search failed." });
    }
  }

  function clearSearch() {
    setQuery("");
    setSearch({ status: "idle" });
  }

  return (
    <main>
      <Container className="py-8">
        <h1 className="mb-2 text-center text-3xl font-semibold text-gray-900 md:text-4xl">Find activewear in plain words</h1>
        <p className="mb-6 text-center text-sm text-gray-500">
          Describe the activity, fit, fabric or budget. For a back-and-forth, try the{" "}
          <Link href="/chat" className="text-blue-600 hover:underline">
            assistant
          </Link>
          .
        </p>

        <form onSubmit={handleSearch} role="search" className="mx-auto mb-8 flex max-w-xl gap-2">
          <label htmlFor="search" className="sr-only">
            Search products
          </label>
          <div className="relative flex-1">
            <input
              id="search"
              type="search"
              value={query}
              maxLength={500}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. squat-proof leggings under ₹2,000"
              className="w-full rounded-lg border border-gray-300 px-4 py-2 pr-9 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {query && (
              <button
                type="button"
                onClick={clearSearch}
                aria-label="Clear search"
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-1 text-gray-400 hover:text-gray-700"
              >
                ×
              </button>
            )}
          </div>
          <Button type="submit" disabled={!query.trim() || search.status === "loading"}>
            Search
          </Button>
        </form>

        <section aria-live="polite">
          {search.status === "idle" && <CatalogView catalog={catalog} onRetry={retryCatalog} />}

          {search.status === "loading" && <ProductGridSkeleton />}

          {search.status === "error" && (
            <div className="py-8 text-center text-sm">
              <p className="mb-3 text-red-700">{search.message}</p>
              <Button variant="secondary" onClick={() => handleSearch()}>
                Try again
              </Button>
            </div>
          )}

          {search.status === "ok" && (
            <>
              <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-sm text-gray-700">{search.res.message}</p>
                <button type="button" onClick={clearSearch} className="text-sm text-blue-600 hover:underline">
                  ← Back to all products
                </button>
              </div>
              <ProductGrid
                products={search.res.results}
                variant="chat"
                emptyMessage={`No matches for “${search.query}”.`}
              />
            </>
          )}
        </section>
      </Container>
    </main>
  );
}

function CatalogView({ catalog, onRetry }: { catalog: Catalog; onRetry: () => void }) {
  if (catalog.status === "loading") return <ProductGridSkeleton />;
  if (catalog.status === "error") {
    return (
      <div className="py-8 text-center text-sm">
        <p className="mb-3 text-red-700">Couldn&apos;t load products: {catalog.message}</p>
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      </div>
    );
  }
  return <ProductGrid products={catalog.products} />;
}
