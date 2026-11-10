import Link from "next/link";
import type { Product } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import ProductImage from "./ProductImage";

export const CARD =
  "group flex flex-col rounded-2xl bg-white p-2 ring-1 ring-gray-100 transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-brand-100 hover:ring-brand-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400";

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link href={`/products/${product.product_id}`} className={CARD}>
      <div className="relative mb-3">
        <ProductImage
          src={product.image_url}
          alt={product.title}
          sizes="(min-width: 1024px) 25vw, (min-width: 768px) 33vw, 50vw"
          className="aspect-[4/5] rounded-xl"
          zoom
        />
        {product.category && (
          <span className="absolute left-2 top-2 rounded-full bg-white/90 px-2.5 py-0.5 text-[11px] font-semibold text-gray-700 backdrop-blur">
            {product.category}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col px-1 pb-1">
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-gray-900">{product.title}</h3>
        <p className="mt-auto pt-1.5 text-base font-bold text-brand-600">{formatPrice(product.price)}</p>
      </div>
    </Link>
  );
}
