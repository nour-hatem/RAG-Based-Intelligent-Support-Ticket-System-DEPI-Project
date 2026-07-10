"use client";

import { Button } from "@heroui/react";
import { ChevronLeft, ChevronRight, Plus, X } from "lucide-react";
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
  function handleSelect(id: string) {
    onSelect(id);
    // On mobile (sidebar is used as drawer), close after selecting
    if (window.innerWidth < 768 && !collapsed) {
      onToggleCollapsed();
    }
  }

  return (
    <>
      {/* Mobile overlay backdrop */}
      {!collapsed && (
        <div
          className="fixed inset-0 z-20 bg-black/40 backdrop-blur-sm md:hidden"
          onClick={onToggleCollapsed}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <div
        className={`
          fixed inset-y-0 left-0 z-30 flex flex-col
          border-r border-default-200 bg-surface-secondary
          transition-all duration-300 ease-in-out
          md:relative md:z-auto md:inset-auto md:h-full
          ${collapsed
            ? "-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden md:opacity-0 md:border-0"
            : "translate-x-0 w-72 opacity-100"
          }
        `}
      >
        <div className="flex items-center justify-between gap-2 border-b border-default-200 p-4">
          <div>
            <p className="font-semibold leading-tight">Triage</p>
            <p className="text-xs text-muted">Ticket routing history</p>
          </div>
          {/* Close button — visible only on mobile */}
          <button
            onClick={onToggleCollapsed}
            className="flex h-7 w-7 items-center justify-center rounded-full text-muted hover:text-foreground md:hidden"
            aria-label="Close sidebar"
          >
            <X size={16} />
          </button>
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
                  onClick={() => handleSelect(c.id)}
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
      </div>

      {/* Desktop collapse toggle button — hidden on mobile */}
      <button
        onClick={onToggleCollapsed}
        title={collapsed ? "Show sidebar" : "Hide sidebar"}
        aria-label={collapsed ? "Show sidebar" : "Hide sidebar"}
        className={`
          absolute top-1/2 z-10 -translate-y-1/2
          hidden md:flex
          h-7 w-7 items-center justify-center
          rounded-full border border-default-200
          bg-foreground text-background shadow-lg
          transition-all duration-300 hover:scale-105
          ${collapsed ? "left-2" : "left-[calc(18rem-0.75rem)]"}
        `}
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </>
  );
}
