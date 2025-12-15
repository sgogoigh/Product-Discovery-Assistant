import Link from "next/link";
import type { Product } from "@/lib/types";

export default function ProductCard({
  product,
}: {
  product: Product;
}) {
  return (
    <Link
      href={`/products/${product.product_id}`}
      className="border rounded-lg p-4 hover:shadow transition block"
    >
      <img
        src={product.image_url}
        alt={product.title}
        className="w-full h-40 object-cover mb-3 rounded"
        loading="lazy"
      />

      <h3 className="font-medium">
        {product.title}
      </h3>

      <p className="text-sm text-gray-600">
        {product.category}
      </p>

      <p className="mt-1 font-semibold">
        ₹{product.price}
      </p>
    </Link>
  );
}
