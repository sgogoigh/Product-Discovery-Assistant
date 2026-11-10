import Link from "next/link";
import type { ChatProductCard as Product } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import ProductImage from "@/components/product/ProductImage";

export default function ChatProductCard({ product }: { product: Product }) {
  return (
    <Link
      href={`/products/${product.product_id}`}
      className="group flex flex-col rounded-lg border border-gray-200 bg-white p-3 transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
    >
      <ProductImage
        src={product.image_url}
        alt={product.title}
        sizes="(min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw"
        className="mb-3 aspect-[4/5] rounded"
      />
      <h3 className="text-sm font-semibold leading-snug text-gray-900 group-hover:underline">{product.title}</h3>
      {product.explanation && <p className="mt-1 line-clamp-3 text-xs text-gray-600">{product.explanation}</p>}
      <p className="mt-auto pt-2 text-sm font-bold text-gray-900">{formatPrice(product.price)}</p>
    </Link>
  );
}
