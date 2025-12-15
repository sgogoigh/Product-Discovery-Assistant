import { API_BASE_URL } from "./config";
import type { Product, ChatResponse } from "./types";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// GET /api/products
export async function getProducts(): Promise<Product[]> {
  const res = await fetch(`${API_BASE_URL}/api/products`, {
    cache: "no-store",
  });
  return handleResponse<Product[]>(res);
}

// GET /api/products/{id}
export async function getProduct(product_id: number): Promise<Product> {
  const res = await fetch(
    `${API_BASE_URL}/api/products/${product_id}`,
    { cache: "no-store" }
  );
  return handleResponse<Product>(res);
}

// POST /api/chat
export async function chat(
  query: string,
  context?: any
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      context,
    }),
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function chatSearch(query: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Chat request failed");
  }

  return (await res.json()) as ChatResponse;
}
