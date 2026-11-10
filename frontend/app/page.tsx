"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { ChatResponse, Product } from "@/lib/types";
import { chat, getProducts } from "@/lib/api";
import ProductGrid from "@/components/product/ProductGrid";
import Container from "@/components/layout/Container";
import Button from "@/components/ui/Button";
import { EmptyState, ProductGridSkeleton } from "@/components/ui/Loading";
import { NeuAvatar } from "@/components/chat/ChatBubble";

type Catalog = { status: "loading" } | { status: "error"; message: string } | { status: "ok"; products: Product[] };
type Search =
  | { status: "idle" }
  | { status: "loading"; query: string }
  | { status: "error"; query: string; message: string }
  | { status: "ok"; query: string; res: ChatResponse };
type Sort = "featured" | "price-asc" | "price-desc";

const EXAMPLES = [
  "Squat-proof leggings under ₹2,000",
  "Breathable sports bra for running",
  "Shorts with pockets",
  "Something cute for pilates",
];

export default function HomePage() {
  const [catalog, setCatalog] = useState<Catalog>({ status: "loading" });
  const [search, setSearch] = useState<Search>({ status: "idle" });
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [sort, setSort] = useState<Sort>("featured");

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

  async function runSearch(text: string) {
    const q = text.trim();
    if (!q || search.status === "loading") return;
    setQuery(q);
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
      <section className="bg-hero border-b border-brand-100/60">
        <Container className="py-12 text-center md:py-16">
          <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-accent-700 ring-1 ring-accent-100">
            <span aria-hidden>✨</span> AI-powered activewear search
          </p>
          <h1 className="mx-auto mb-3 max-w-2xl text-4xl font-extrabold tracking-tight text-gray-900 md:text-5xl">
            Find activewear in <span className="text-brand-gradient">plain words</span>
          </h1>
          <p className="mx-auto mb-8 max-w-xl text-base text-gray-600">
            Describe the activity, fit, fabric or budget — we&apos;ll match it to the right pieces and tell you why.
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              void runSearch(query);
            }}
            role="search"
            className="mx-auto flex max-w-2xl items-center gap-2 rounded-full bg-white p-2 pl-5 shadow-lg shadow-brand-100 ring-1 ring-gray-100 focus-within:ring-2 focus-within:ring-brand-300"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5 shrink-0 text-brand-400" aria-hidden>
              <path
                fillRule="evenodd"
                d="M9 3.5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11ZM2 9a7 7 0 1 1 12.45 4.4l3.08 3.07a.75.75 0 1 1-1.06 1.06l-3.07-3.08A7 7 0 0 1 2 9Z"
                clipRule="evenodd"
              />
            </svg>
            <label htmlFor="search" className="sr-only">
              Search products
            </label>
            <input
              id="search"
              type="search"
              value={query}
              maxLength={500}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. high-waisted leggings for yoga"
              className="min-w-0 flex-1 bg-transparent py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none md:text-base"
            />
            <Button type="submit" disabled={!query.trim() || search.status === "loading"} className="md:px-6 md:py-2.5">
              {search.status === "loading" ? "Searching…" : "Search"}
            </Button>
          </form>

          <div className="mx-auto mt-4 flex max-w-2xl flex-wrap justify-center gap-2" aria-label="Example searches">
            <span className="py-1 text-xs text-gray-500">Try:</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => runSearch(ex)}
                disabled={search.status === "loading"}
                className="rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-gray-700 ring-1 ring-gray-200 transition hover:bg-brand-50 hover:text-brand-700 hover:ring-brand-200 disabled:opacity-50"
              >
                {ex}
              </button>
            ))}
          </div>
        </Container>
      </section>

      <Container className="py-10">
        <section aria-live="polite">
          {search.status === "idle" && (
            <CatalogView
              catalog={catalog}
              onRetry={retryCatalog}
              category={category}
              setCategory={setCategory}
              sort={sort}
              setSort={setSort}
            />
          )}

          {search.status === "loading" && <ProductGridSkeleton />}

          {search.status === "error" && (
            <EmptyState title="That search didn't go through">
              <p className="mb-4">{search.message}</p>
              <Button variant="secondary" onClick={() => runSearch(search.query)}>
                Try again
              </Button>
            </EmptyState>
          )}

          {search.status === "ok" && (
            <>
              <div className="mb-6 flex flex-col gap-3 rounded-2xl bg-white p-4 ring-1 ring-gray-100 sm:flex-row sm:items-center">
                <NeuAvatar className="h-10 w-10 text-sm" />
                <p className="flex-1 text-sm leading-relaxed text-gray-700">{search.res.message}</p>
                <div className="flex shrink-0 gap-2">
                  <Link
                    href="/chat"
                    className="rounded-full bg-accent-50 px-4 py-2 text-xs font-semibold text-accent-700 transition hover:bg-accent-100"
                  >
                    Refine with Neu →
                  </Link>
                  <Button variant="secondary" className="px-4 text-xs" onClick={clearSearch}>
                    All products
                  </Button>
                </div>
              </div>
              <ProductGrid
                products={search.res.results}
                variant="chat"
                emptyMessage={`No matches for “${search.query}”.`}
              />
            </>
          )}
        </section>

        <AssistantPromo />
      </Container>
    </main>
  );
}

type CatalogProps = {
  catalog: Catalog;
  onRetry: () => void;
  category: string | null;
  setCategory: (c: string | null) => void;
  sort: Sort;
  setSort: (s: Sort) => void;
};

function CatalogView({ catalog, onRetry, category, setCategory, sort, setSort }: CatalogProps) {
  const products = useMemo(() => (catalog.status === "ok" ? catalog.products : []), [catalog]);
  const categories = useMemo(
    () => [...new Set(products.map((p) => p.category).filter(Boolean))].sort(),
    [products],
  );
  const shown = useMemo(() => {
    const list = category ? products.filter((p) => p.category === category) : [...products];
    if (sort !== "featured") {
      const dir = sort === "price-asc" ? 1 : -1;
      list.sort((a, b) => dir * ((a.price ?? Infinity) - (b.price ?? Infinity)));
    }
    return list;
  }, [products, category, sort]);

  if (catalog.status === "loading") return <ProductGridSkeleton />;
  if (catalog.status === "error") {
    return (
      <EmptyState title="Couldn't load products">
        <p className="mb-4">{catalog.message}</p>
        <Button variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      </EmptyState>
    );
  }

  const pill = (active: boolean) =>
    `shrink-0 rounded-full px-4 py-1.5 text-sm font-medium transition ${
      active ? "bg-gray-900 text-white" : "bg-white text-gray-700 ring-1 ring-gray-200 hover:ring-brand-300 hover:text-brand-700"
    }`;

  return (
    <>
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight text-gray-900">Shop the collection</h2>
          <p className="text-sm text-gray-500">
            {shown.length} {shown.length === 1 ? "style" : "styles"}
            {category ? ` in ${category}` : ""}
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          Sort
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as Sort)}
            className="rounded-full bg-white px-3 py-1.5 text-sm text-gray-900 ring-1 ring-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-300"
          >
            <option value="featured">Featured</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
          </select>
        </label>
      </div>

      <div className="-mx-4 mb-6 flex gap-2 overflow-x-auto px-4 pb-1" role="group" aria-label="Filter by category">
        <button type="button" onClick={() => setCategory(null)} aria-pressed={category === null} className={pill(category === null)}>
          All
        </button>
        {categories.map((c) => (
          <button key={c} type="button" onClick={() => setCategory(c)} aria-pressed={category === c} className={pill(category === c)}>
            {c}
          </button>
        ))}
      </div>

      <ProductGrid products={shown} />
    </>
  );
}

function AssistantPromo() {
  return (
    <section className="bg-brand-gradient mt-14 overflow-hidden rounded-3xl p-8 text-white md:p-10">
      <div className="flex flex-col items-start gap-6 md:flex-row md:items-center md:justify-between">
        <div className="max-w-xl">
          <h2 className="mb-2 text-2xl font-extrabold tracking-tight md:text-3xl">Not sure what you need?</h2>
          <p className="text-white/90">
            Chat with Neu, your activewear stylist. Say what you&apos;re training for, then steer with things like
            &ldquo;cheaper&rdquo; or &ldquo;only shorts&rdquo;.
          </p>
        </div>
        <Link
          href="/chat"
          className="shrink-0 rounded-full bg-white px-6 py-3 text-sm font-bold text-brand-600 shadow-lg transition hover:-translate-y-0.5"
        >
          Start chatting →
        </Link>
      </div>
    </section>
  );
}
