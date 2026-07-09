"use client";

import { useEffect, useRef, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatInput } from "@/components/ChatInput";
import { UserMessage } from "@/components/UserMessage";
import { TicketResult } from "@/components/TicketResult";
import { ErrorMessage } from "@/components/ErrorMessage";
import { ThinkingBubble } from "@/components/ThinkingBubble";
import { ThemeToggle } from "@/components/ThemeToggle";
import { checkHealth, submitTicket, ApiError } from "@/lib/api";
import type { ChatMessage, Conversation } from "@/lib/types";

function makeId() {
  return Math.random().toString(36).slice(2, 10);
}

function newConversation(): Conversation {
  return { id: makeId(), title: "New ticket", messages: [] };
}

export default function Page() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [isSending, setIsSending] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const first = newConversation();
    setConversations([first]);
    setActiveId(first.id);
    checkHealth().then(setBackendOnline);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [conversations, activeId]);

  const active = conversations.find((c) => c.id === activeId) ?? conversations[0];

  function updateActive(updater: (c: Conversation) => Conversation) {
    setConversations((prev) => prev.map((c) => (c.id === activeId ? updater(c) : c)));
  }

  function handleNew() {
    const conv = newConversation();
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
  }

  async function handleSubmit(subject: string, body: string) {
    if (!active) return;

    const userMsg: ChatMessage = {
      id: makeId(),
      role: "user",
      text: body,
      createdAt: Date.now(),
    };

    updateActive((c) => ({
      ...c,
      title: c.messages.length === 0 ? (subject || body).slice(0, 40) : c.title,
      messages: [...c.messages, userMsg],
    }));

    setIsSending(true);
    try {
      const result = await submitTicket({ subject: subject || undefined, body });
      const aiMsg: ChatMessage = { id: makeId(), role: "assistant", result, createdAt: Date.now() };
      updateActive((c) => ({ ...c, messages: [...c.messages, aiMsg] }));
      setBackendOnline(true);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unexpected error. Please try again.";
      const errMsg: ChatMessage = { id: makeId(), role: "error", error: message, createdAt: Date.now() };
      updateActive((c) => ({ ...c, messages: [...c.messages, errMsg] }));
      if (err instanceof ApiError && err.message.includes("unavailable")) {
        setBackendOnline(false);
      }
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNew}
      />

      <main className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-default-200 px-6 py-3">
          <div>
            <h1 className="text-sm font-semibold">Support Ticket Triage</h1>
            <p className="text-xs text-muted">
              {backendOnline === null
                ? "Checking backend…"
                : backendOnline
                  ? "Backend online"
                  : "Backend unavailable"}
            </p>
          </div>
          <ThemeToggle />
        </header>

        <div ref={scrollRef} className="thin-scroll flex-1 space-y-4 overflow-y-auto px-6 py-6">
          {active?.messages.length === 0 && (
            <div className="mx-auto mt-16 max-w-md text-center text-sm text-muted">
              Type a customer's message below. Triage will predict the right queue and draft a
              reply, or flag it for human review if it isn't confident enough.
            </div>
          )}

          {active?.messages.map((m) => {
            if (m.role === "user") return <UserMessage key={m.id} text={m.text ?? ""} />;
            if (m.role === "assistant" && m.result) return <TicketResult key={m.id} result={m.result} />;
            if (m.role === "error") return <ErrorMessage key={m.id} message={m.error ?? "Unknown error"} />;
            return null;
          })}

          {isSending && <ThinkingBubble />}
        </div>

        <ChatInput onSubmit={handleSubmit} isSending={isSending} />
      </main>
    </div>
  );
}
