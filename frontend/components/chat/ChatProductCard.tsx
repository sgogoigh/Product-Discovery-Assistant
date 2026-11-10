import Link from "next/link";
import type { ChatProductCard as Product } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import ProductImage from "@/components/product/ProductImage";
import { CARD } from "@/components/product/ProductCard";

export default function ChatProductCard({ product }: { product: Product }) {
  return (
    <Link href={`/products/${product.product_id}`} className={CARD}>
      <ProductImage
        src={product.image_url}
        alt={product.title}
        sizes="(min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw"
        className="mb-2 aspect-[4/5] rounded-xl"
        zoom
      />
      <div className="flex flex-1 flex-col px-1 pb-1">
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-gray-900">{product.title}</h3>
        {product.explanation && (
          <p className="mt-1.5 line-clamp-3 rounded-lg bg-accent-50 px-2 py-1.5 text-xs leading-snug text-accent-700">
            <span aria-hidden>✨ </span>
            {product.explanation}
          </p>
        )}
        <p className="mt-auto pt-2 text-base font-bold text-brand-600">{formatPrice(product.price)}</p>
      </div>
    </Link>
  );
}
