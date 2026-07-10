"use client";

import { useEffect, useRef, useState } from "react";
import { Button, Chip } from "@heroui/react";
import { Menu, Sparkles } from "lucide-react";
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
  // On desktop, collapsed = false by default; on mobile, collapsed = true (drawer closed)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initialise collapsed state based on viewport width
  useEffect(() => {
    if (window.innerWidth < 768) setSidebarCollapsed(true);
  }, []);

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
    /* Outer shell: sidebar + main side-by-side on md+; stacked (sidebar as overlay) on mobile */
    <div className="relative flex h-screen w-full overflow-hidden bg-white text-foreground dark:bg-gray-950">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNew}
        collapsed={sidebarCollapsed}
        onToggleCollapsed={() => setSidebarCollapsed((v) => !v)}
      />

      <main className="flex flex-1 flex-col overflow-hidden">
        {/* ── Header ────────────────────────────────────────────── */}
        <header className="flex items-center justify-between gap-2 border-b border-blue-100 bg-white/90 px-3 py-3 backdrop-blur-sm dark:border-blue-900/30 dark:bg-gray-950/90 sm:px-6 sm:py-4">
          <div className="flex items-center gap-3">
            {/* Hamburger — shown on mobile when sidebar is closed; upgraded to HeroUI Button */}
            <Button
              variant="ghost"
              size="sm"
              isIconOnly
              onPress={() => setSidebarCollapsed(false)}
              aria-label="Open sidebar"
              className={`text-gray-400 hover:text-blue-600 md:hidden ${!sidebarCollapsed ? "invisible" : ""}`}
            >
              <Menu size={20} />
            </Button>

            <div>
              <h1 className="text-lg font-black tracking-tight text-blue-700 dark:text-blue-300 sm:text-2xl">
                Triage
              </h1>
              <p className="hidden text-xs text-gray-400 sm:block">
                Automated AI router &amp; RAG assistant
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />

            {/* Status chip — blue-only scheme (no green/red) */}
            <div className="flex items-center gap-1.5 rounded-full border border-blue-100 bg-blue-50/60 px-2.5 py-1 text-xs dark:border-blue-900/30 dark:bg-blue-950/30">
              <span
                className={`status-dot ${
                  backendOnline === null
                    ? "checking"
                    : backendOnline
                      ? "online"
                      : "offline"
                }`}
              />
              <span className="font-medium text-blue-700 dark:text-blue-300">
                {backendOnline === null
                  ? "Checking…"
                  : backendOnline
                    ? "Online"
                    : "Offline"}
              </span>
            </div>
          </div>
        </header>

        {/* ── Message list ──────────────────────────────────────── */}
        <div
          ref={scrollRef}
          className="thin-scroll flex-1 space-y-4 overflow-y-auto px-3 py-4 sm:px-6 sm:py-6"
        >
          {/* Empty state */}
          {active?.messages.length === 0 && (
            <div className="mx-auto mt-8 flex max-w-sm flex-col items-center gap-5 text-center sm:mt-16">
              {/* Blue-only gradient icon — violet removed */}
              <div className="flex h-14 w-14 rotate-3 items-center justify-center rounded-2xl bg-gradient-to-tr from-blue-600 to-blue-400 text-white shadow-lg shadow-blue-500/25 sm:h-16 sm:w-16">
                <Sparkles size={24} className="sm:hidden" />
                <Sparkles size={28} className="hidden sm:block" />
              </div>
              <div>
                <h3 className="text-lg font-black tracking-tight text-blue-700 dark:text-blue-300 sm:text-xl">
                  Ready for triage
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-400">
                  Type a customer&apos;s message below. Triage will predict the right queue,
                  calculate confidence, and draft a reply — or flag it for human review if it
                  isn&apos;t confident enough.
                </p>
              </div>
            </div>
          )}

          {/* Message rendering — all logic untouched */}
          {active?.messages.map((m) => {
            if (m.role === "user")
              return <UserMessage key={m.id} text={m.text ?? ""} createdAt={m.createdAt} />;
            if (m.role === "assistant" && m.result)
              return <TicketResult key={m.id} result={m.result} createdAt={m.createdAt} />;
            if (m.role === "error")
              return <ErrorMessage key={m.id} message={m.error ?? "Unknown error"} />;
            return null;
          })}

          {isSending && <ThinkingBubble />}
        </div>

        <ChatInput onSubmit={handleSubmit} isSending={isSending} />
      </main>
    </div>
  );
}
