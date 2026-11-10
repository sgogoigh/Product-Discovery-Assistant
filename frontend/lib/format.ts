const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export function formatPrice(price: number | null | undefined): string {
  return typeof price === "number" && Number.isFinite(price) ? inr.format(price) : "Price unavailable";
}
