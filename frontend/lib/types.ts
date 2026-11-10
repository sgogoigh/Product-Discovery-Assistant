export type Feature = {
  section: string;
  title?: string | null;
  description: string;
};

export type Product = {
  product_id: number;
  title: string;
  price: number | null;
  category: string;
  description?: string | null;
  image_url: string;
  source_url: string;
  features: Feature[];
};

export type ChatProductCard = {
  product_id: number;
  title: string;
  price: number | null;
  category: string;
  image_url: string;
  source_url: string;
  match_field: string;
  snippet: string;
  score: number;
  explanation?: string | null;
};

export type Constraints = {
  category: string | null;
  min_price: number | null;
  max_price: number | null;
};

/** Opaque conversation state: send back exactly what the server returned. */
export type ChatContext = Record<string, unknown>;

export type ChatResponse = {
  query: string;
  message: string;
  results: ChatProductCard[];
  suggestions: string[];
  constraints: Constraints;
  context: ChatContext;
};
