export type Feature = {
  section: string
  title?: string | null
  description: string
}

export type Product = {
  product_id: number
  title: string
  price: number
  category: string
  image_url: string
  source_url: string
  features: Feature[]
}

export type ChatProductCard = {
  product_id: number
  title: string
  price: number | null
  category: string
  image_url: string
  source_url: string
  match_field: string
  snippet: string
  score: number
  explanation?: string
}

export type ChatResponse = {
  query: string;
  results: ChatProductCard[];
  clarification?: string;
  context?: Record<string, any>;
};