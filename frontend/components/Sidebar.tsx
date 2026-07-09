"use client";

import { Button } from "@heroui/react";
import type { Conversation } from "@/lib/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
}

export function Sidebar({ conversations, activeId, onSelect, onNew }: SidebarProps) {
  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-default-200 bg-surface-secondary">
      <div className="flex items-center justify-between gap-2 border-b border-default-200 p-4">
        <div>
          <p className="font-semibold leading-tight">Triage</p>
          <p className="text-xs text-muted">Ticket routing history</p>
        </div>
      </div>

      <div className="p-3">
        <Button variant="primary" className="w-full" onPress={onNew}>
          + New ticket
        </Button>
      </div>

      <nav className="thin-scroll flex-1 overflow-y-auto px-2 pb-4">
        {conversations.length === 0 && (
          <p className="px-2 py-6 text-center text-sm text-muted">No tickets yet.</p>
        )}
        <ul className="flex flex-col gap-1">
          {conversations.map((c) => (
            <li key={c.id}>
              <button
                onClick={() => onSelect(c.id)}
                className={
                  "w-full truncate rounded-lg px-3 py-2 text-left text-sm transition-colors " +
                  (c.id === activeId
                    ? "bg-surface-tertiary font-medium text-foreground"
                    : "text-muted hover:bg-surface-tertiary/60")
                }
                title={c.title}
              >
                {c.title || "Untitled ticket"}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
