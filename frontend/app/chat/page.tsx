import type { Metadata } from "next";
import ChatWindow from "@/components/chat/ChatWindow";
import Container from "@/components/layout/Container";

export const metadata: Metadata = { title: "Chat with Neu" };

export default function ChatPage() {
  // 3.5rem = header height
  return (
    <main className="bg-hero h-[calc(100dvh-3.5rem)] py-4">
      <Container className="h-full max-w-5xl">
        <ChatWindow />
      </Container>
    </main>
  );
}
