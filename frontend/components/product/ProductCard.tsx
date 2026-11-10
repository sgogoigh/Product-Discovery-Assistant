import Link from "next/link";
import type { Product } from "@/lib/types";
import { formatPrice } from "@/lib/format";
import ProductImage from "./ProductImage";

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link
      href={`/products/${product.product_id}`}
      className="group block rounded-lg border border-gray-200 bg-white p-3 transition hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
    >
      <ProductImage
        src={product.image_url}
        alt={product.title}
        sizes="(min-width: 1024px) 25vw, (min-width: 768px) 33vw, 50vw"
        className="mb-3 aspect-[4/5] rounded"
      />
      <h3 className="font-medium leading-snug text-gray-900 group-hover:underline">{product.title}</h3>
      {product.category && <p className="text-sm text-gray-500">{product.category}</p>}
      <p className="mt-1 font-semibold text-gray-900">{formatPrice(product.price)}</p>
    </Link>
  );
}
