import type { ChatProductCard, Product } from "@/lib/types";
import ProductCard from "@/components/product/ProductCard";
import ChatProductCardComponent from "@/components/chat/ChatProductCard";

type Props =
  | { products: Product[]; variant?: "catalog"; emptyMessage?: string }
  | { products: ChatProductCard[]; variant: "chat"; emptyMessage?: string };

const GRID = "grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4";

export default function ProductGrid(props: Props) {
  if (!props.products.length) {
    return <p className="py-8 text-center text-sm text-gray-500">{props.emptyMessage ?? "No products available."}</p>;
  }

  if (props.variant === "chat") {
    return (
      <div className={GRID}>
        {props.products.map((p) => (
          <ChatProductCardComponent key={p.product_id} product={p} />
        ))}
      </div>
    );
  }

  return (
    <div className={GRID}>
      {props.products.map((p) => (
        <ProductCard key={p.product_id} product={p} />
      ))}
    </div>
  );
}
