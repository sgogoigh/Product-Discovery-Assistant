import Link from "next/link";
import type { ChatProductCard as Product } from "@/lib/types";

export default function ChatProductCard({
  product,
}: {
  product: Product;
}) {
  return (
    <Link
      href={`/products/${product.product_id}`}
      className="block rounded-lg border border-gray-200 bg-white p-4 hover:shadow-sm transition"
    >
      {/* Image */}
      <div className="flex justify-center mb-3">
        <img
          src={product.image_url}
          alt={product.title}
          className="h-36 object-contain"
        />
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-gray-900 leading-snug mb-1">
        {product.title}
      </h3>

      {/* Explanation (helper text) */}
      {product.explanation && (
        <p className="text-xs text-gray-600 mb-2 line-clamp-2">
          {product.explanation}
        </p>
      )}

      {/* Price */}
      <div className="mt-2">
        <span className="text-sm font-bold text-gray-900">
          {product.price ? `₹${product.price}` : "Price unavailable"}
        </span>
      </div>
    </Link>
  );
}