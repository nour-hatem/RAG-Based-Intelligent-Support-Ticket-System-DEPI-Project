"use client";

import { Button } from "@heroui/react";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import type { Conversation } from "@/lib/types";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  collapsed,
  onToggleCollapsed,
}: SidebarProps) {
  return (
    <div className="relative">
      <aside
        className={`flex h-full flex-col border-r border-default-200 bg-surface-secondary transition-all duration-300 ${
          collapsed ? "w-0 overflow-hidden opacity-0" : "w-72 opacity-100"
        }`}
      >
        <div className="flex items-center justify-between gap-2 border-b border-default-200 p-4">
          <div>
            <p className="font-semibold leading-tight">Triage</p>
            <p className="text-xs text-muted">Ticket routing history</p>
          </div>
        </div>

        <div className="p-3">
          <Button variant="primary" fullWidth onPress={onNew}>
            <Plus size={16} /> New ticket
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

      <button
        onClick={onToggleCollapsed}
        title={collapsed ? "Show sidebar" : "Hide sidebar"}
        className="absolute bottom-4 -right-3 z-10 flex h-7 w-7 items-center justify-center rounded-full border border-default-200 bg-foreground text-background shadow-lg transition-transform hover:scale-105"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </div>
  );
}
