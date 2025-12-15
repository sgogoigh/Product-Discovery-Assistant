# AI Product Discovery Assistant Frontend

This is a **Next.js (App Router)** application that provides a clean UI for an **AI-powered product discovery system** backed by a FastAPI RAG + agent backend.

The frontend is intentionally lightweight and focuses only on **presentation and UX**. All reasoning, retrieval, filtering, and decision-making happen in the backend.

---

## Features

### 1. Home Page (Semantic Search)
- Natural language search bar
- Direct RAG-based product retrieval
- Compact product grid for quick scanning
- Click-through to product detail pages

### 2. AI Chat Assistant
- Conversational product discovery
- Multi-turn refinement (e.g. “cheaper”, “under 500”)
- Clarification prompts when needed
- Bot response shown **before** product cards
- User and bot messages clearly distinguishable

---

## Tech Stack

- **Next.js 16** (App Router)
- **TypeScript**
- **Tailwind CSS v4**
- **Fetch API** for backend communication

---

## Folder Structure

```
frontend/
├── app/
│ ├── layout.tsx # Global layout + chat launcher
│ ├── globals.css # Global styles
│ ├── page.tsx # Home (RAG search)
│ ├── products/
│ │ └── [product_id]/
│ │ └── page.tsx # Product detail page
│ └── chat/
│ └── page.tsx # Chat interface
│
├── components/
│ ├── chat/
│ │ ├── ChatWindow.tsx
│ │ ├── ChatBubble.tsx
│ │ ├── ChatInput.tsx
│ │ ├── ChatProductCard.tsx
│ │ └── ChatLauncher.tsx
│ ├── product/
│ │ ├── ProductGrid.tsx
│ │ ├── ProductCard.tsx
│ │ └── FeatureSection.tsx
│ └── ui/
│ ├── Button.tsx
│ └── Loading.tsx
│
├── lib/
│ ├── api.ts # FastAPI calls
│ ├── types.ts # Shared types
│ └── config.ts # API base URL
│
├── public/
├── next.config.js
├── tailwind.config.ts
├── package.json
└── README.md
```

---

## Backend Integration

The frontend communicates with the FastAPI backend via:

- `POST /api/chat` — agent-driven chat + RAG
- `GET /api/products` — product listing
- `GET /api/products/{id}` — product details

All intelligence (agent loop, reasoning, filtering, explanations) is handled by the backend.

---

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```
Ensure the backend is running and the API base URL is correctly set.

---

## Notes

- No business logic is implemented in the frontend
- UI is designed for clarity during demos
- Console noise is removed for clean presentation

> Made by Sunny Gogoi