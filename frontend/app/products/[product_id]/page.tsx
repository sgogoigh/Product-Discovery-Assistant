import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getProduct } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import type { Product } from "@/lib/types";
import Container from "@/components/layout/Container";
import FeatureSection from "@/components/product/FeatureSection";
import ProductImage from "@/components/product/ProductImage";

type PageProps = {
  params: Promise<{ product_id: string }>;
};

async function load(id: string): Promise<Product | "error"> {
  const productId = Number(id);
  if (!Number.isInteger(productId) || productId <= 0) notFound();
  try {
    return await getProduct(productId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    return "error";
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const product = await load((await params).product_id);
  return product === "error" ? { title: "Product" } : { title: product.title, description: product.description ?? undefined };
}

export default async function ProductDetailPage({ params }: PageProps) {
  const product = await load((await params).product_id);

  if (product === "error") {
    return (
      <main>
        <Container className="py-10">
          <p className="mb-4 text-red-700">We couldn&apos;t load this product right now. Please try again shortly.</p>
          <Link href="/" className="text-blue-600 hover:underline">
            ← Back to all products
          </Link>
        </Container>
      </main>
    );
  }

  return (
    <main>
      <Container className="max-w-5xl py-6">
        <Link href="/" className="mb-4 inline-block text-sm text-blue-600 hover:underline">
          ← Back to all products
        </Link>

        <div className="grid gap-8 md:grid-cols-2">
          <ProductImage
            src={product.image_url}
            alt={product.title}
            sizes="(min-width: 768px) 50vw, 100vw"
            className="aspect-[4/5] rounded-lg border border-gray-200"
            priority
          />

          <div>
            <h1 className="mb-2 text-2xl font-semibold text-gray-900">{product.title}</h1>
            <p className="mb-4 text-gray-600">
              <span className="text-lg font-semibold text-gray-900">{formatPrice(product.price)}</span>
              {product.category && (
                <>
                  <span className="mx-2" aria-hidden>
                    •
                  </span>
                  <span>{product.category}</span>
                </>
              )}
            </p>

            {product.description && <p className="mb-6 leading-relaxed text-gray-700">{product.description}</p>}

            {product.source_url && (
              <a
                href={product.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                View on the store ↗
              </a>
            )}
          </div>
        </div>

        <section className="mt-10 space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Features</h2>
          <FeatureSection features={product.features} />
        </section>
      </Container>
    </main>
  );
}
