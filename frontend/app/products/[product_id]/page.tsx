import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getProduct } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import type { Product } from "@/lib/types";
import Container from "@/components/layout/Container";
import FeatureSection from "@/components/product/FeatureSection";
import ProductImage from "@/components/product/ProductImage";
import { EmptyState } from "@/components/ui/Loading";

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

const backLink = "inline-flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700";

export default async function ProductDetailPage({ params }: PageProps) {
  const product = await load((await params).product_id);

  if (product === "error") {
    return (
      <main>
        <Container className="py-16">
          <EmptyState title="We couldn't load this product right now">
            <p className="mb-4">Please try again in a moment.</p>
            <Link href="/" className={backLink}>
              ← Back to all products
            </Link>
          </EmptyState>
        </Container>
      </main>
    );
  }

  const ask = `Show me something like the ${product.title}`;

  return (
    <main>
      <Container className="max-w-6xl py-6 md:py-10">
        <Link href="/" className={`${backLink} mb-6`}>
          ← Back to all products
        </Link>

        <div className="grid gap-8 md:grid-cols-2 md:gap-12">
          <ProductImage
            src={product.image_url}
            alt={product.title}
            sizes="(min-width: 768px) 50vw, 100vw"
            className="aspect-[4/5] rounded-3xl shadow-xl shadow-brand-100"
            priority
          />

          <div className="md:py-4">
            {product.category && (
              <p className="mb-3 inline-block rounded-full bg-accent-50 px-3 py-1 text-xs font-semibold text-accent-700">
                {product.category}
              </p>
            )}
            <h1 className="mb-3 text-3xl font-extrabold tracking-tight text-gray-900 md:text-4xl">{product.title}</h1>
            <p className="mb-6 text-2xl font-bold text-brand-600">{formatPrice(product.price)}</p>

            {product.description && <p className="mb-8 leading-relaxed text-gray-700">{product.description}</p>}

            <div className="flex flex-wrap gap-3">
              {product.source_url && (
                <a
                  href={product.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-brand-gradient rounded-full px-6 py-3 text-sm font-bold text-white shadow-lg shadow-brand-200 transition hover:-translate-y-0.5"
                >
                  View on the store ↗
                </a>
              )}
              <Link
                href="/chat"
                title={ask}
                className="rounded-full bg-white px-6 py-3 text-sm font-bold text-gray-800 ring-1 ring-gray-200 transition hover:bg-brand-50 hover:text-brand-700 hover:ring-brand-200"
              >
                💬 Ask Neu for similar
              </Link>
            </div>
          </div>
        </div>

        <section className="mt-14">
          <h2 className="mb-5 text-2xl font-extrabold tracking-tight text-gray-900">Why you&apos;ll love it</h2>
          <FeatureSection features={product.features} />
        </section>
      </Container>
    </main>
  );
}
