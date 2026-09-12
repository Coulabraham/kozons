"use client";

import { RequireAuth } from "@/components/auth/require-auth";
import { ChatShell } from "@/components/chat/chat-shell";
import { useConversations } from "@/lib/api/hooks";

function AuthenticatedChatPage() {
  useConversations();
  return <ChatShell />;
}

export default function ChatPage() {
  return (
    <RequireAuth>
      <AuthenticatedChatPage />
    </RequireAuth>
  );
}
