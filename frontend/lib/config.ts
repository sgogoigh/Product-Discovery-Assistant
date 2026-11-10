// NEXT_PUBLIC_* is inlined at build time: set it in Vercel (Project → Settings →
// Environment Variables) and redeploy after changing it.
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");
