import type { Product, ChatProductCard } from "@/lib/types";
import ProductCard from "@/components/product/ProductCard";
import ChatProductCardComponent from "@/components/chat/ChatProductCard";

type CatalogProps = {
  products: Product[];
  variant?: "catalog";
};

type ChatProps = {
  products: ChatProductCard[];
  variant: "chat";
};

type Props = CatalogProps | ChatProps;

export default function ProductGrid(props: Props) {
  if (!props.products || props.products.length === 0) {
    return (
      <p className="text-center text-sm text-gray-500">
        No products available.
      </p>
    );
  }

  // ✅ CHAT RESULTS
  if (props.variant === "chat") {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {props.products.map((p) => (
          <ChatProductCardComponent
            key={p.product_id}
            product={p}
          />
        ))}
      </div>
    );
  }

  // ✅ CATALOG PRODUCTS
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {props.products.map((p) => (
        <ProductCard
          key={p.product_id}
          product={p}
        />
      ))}
    </div>
  );
}