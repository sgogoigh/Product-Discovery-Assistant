import { getProduct } from "@/lib/api";
import type { Product } from "@/lib/types";
import FeatureSection from "@/components/product/FeatureSection";

type PageProps = {
  params: Promise<{
    product_id: string;
  }>;
};

export default async function ProductDetailPage({ params }: PageProps) {
  const { product_id } = await params;

  let product: Product | null = null;

  try {
    product = (await getProduct(Number(product_id))) as Product;
  } catch {
    product = null;
  }

  if (!product) {
    return (
      <main className="p-6">
        <p className="text-gray-500">
          Product not found.
        </p>
      </main>
    );
  }

  return (
    <main className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">
        {product.title}
      </h1>

      <div className="text-gray-600 mb-4">
        <span className="font-medium">₹{product.price}</span>
        <span className="mx-2">•</span>
        <span>{product.category}</span>
      </div>

      <img
        src={product.image_url}
        alt={product.title}
        className="w-full max-h-105 object-contain rounded border mb-6"
        loading="lazy"
      />

      <section className="space-y-6">
        <h2 className="text-xl font-semibold">
          Features
        </h2>
        <FeatureSection features={product.features} />
      </section>

      <div className="mt-8">
        <a
          href={product.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 underline"
        >
          View original product
        </a>
      </div>
    </main>
  );
}