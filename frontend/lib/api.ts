import { API_BASE_URL } from "./config";
import type { ChatContext, ChatResponse, Product } from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 30_000): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: init?.signal ?? AbortSignal.timeout(timeoutMs),
    });
  } catch (err) {
    const timedOut = err instanceof DOMException && err.name === "TimeoutError";
    throw new ApiError(timedOut ? "The server took too long to respond." : "Couldn't reach the server.", 0);
  }
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body?.error === "string") message = body.error;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(message, res.status);
  }
  return (await res.json()) as T;
}

// GET /api/products/
export function getProducts(limit = 200): Promise<Product[]> {
  return request<Product[]>(`/api/products/?limit=${limit}`, { cache: "no-store" });
}

// GET /api/products/{id}
export function getProduct(productId: number): Promise<Product> {
  return request<Product>(`/api/products/${productId}`, { cache: "no-store" });
}

// POST /api/chat/ — used by both the chat assistant and the home search box.
export function chat(query: string, context?: ChatContext | null): Promise<ChatResponse> {
  return request<ChatResponse>(
    "/api/chat/",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, context: context ?? null }),
    },
    45_000,
  );
}
