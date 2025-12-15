"use client";

import { useEffect, useState } from "react";
import type { Product } from "@/lib/types";
import { getProducts, chatSearch } from "@/lib/api";
import ProductGrid from "@/components/product/ProductGrid";

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  // Load initial products (default catalog view)
  useEffect(() => {
    getProducts().then(setProducts).catch(console.error);
  }, []);

  async function handleSearch() {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await chatSearch(query);
      setProducts(res.results ?? []);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Title */}
      <h1 className="text-3xl md:text-4xl font-semibold text-center mb-6">
        Product Discovery
      </h1>

      {/* Search bar */}
      <div className="max-w-xl mx-auto mb-8">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSearch();
          }}
          placeholder="Search products… (e.g. leggings under ₹2,000)"
          className="w-full border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring"
        />
      </div>

      {/* Loading state */}
      {loading && (
        <p className="text-center text-sm text-gray-500 mb-6">
          Searching…
        </p>
      )}

      {/* Product grid */}
      <ProductGrid products={products} />
    </div>
  );
}