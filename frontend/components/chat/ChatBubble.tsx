type ChatBubbleProps = {
  role: "user" | "bot";
  text: string;
};

export default function ChatBubble({ role, text }: ChatBubbleProps) {
  const isUser = role === "user";
  return (
    <div
      className={`flex w-full mb-3 ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`
          max-w-[75%] px-4 py-2 rounded-xl text-sm leading-relaxed
          ${isUser
            ? "bg-blue-600 text-white rounded-br-none"
            : "bg-gray-100 text-gray-900 rounded-bl-none border"}
        `}
      >
        {text}
      </div>
    </div>
  );
}