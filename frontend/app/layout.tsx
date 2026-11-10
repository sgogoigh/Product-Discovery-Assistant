import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import ChatLauncher from "@/components/chat/ChatLauncher";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";

const jakarta = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: { default: "Neusearch — Find activewear in plain words", template: "%s · Neusearch" },
  description:
    "Find activewear in plain language: semantic search and Neu, a conversational shopping assistant built on RAG.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${jakarta.variable} flex min-h-dvh flex-col antialiased`}>
        <Header />
        <div className="flex-1">{children}</div>
        <Footer />
        <ChatLauncher />
      </body>
    </html>
  );
}
