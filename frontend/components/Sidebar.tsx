"use client";

import { Button, Separator } from "@heroui/react";
import { ChevronLeft, ChevronRight, Plus, X, MessageSquare } from "lucide-react";
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
          border-r border-gray-100 bg-white
          transition-all duration-300 ease-in-out
          dark:border-white/5 dark:bg-[#1e1f20]
          md:relative md:z-auto md:inset-auto md:h-full
          ${
            collapsed
              ? "-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden md:opacity-0 md:border-0"
              : "translate-x-0 w-72 opacity-100"
          }
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between gap-2 border-b border-gray-100 p-4 dark:border-white/5">
          <div>
            <p className="font-bold leading-tight text-gray-800 dark:text-gray-100">Triage</p>
            <p className="text-xs text-gray-400">Ticket routing history</p>
          </div>
          {/* Close button — visible only on mobile */}
          <Button
            variant="ghost"
            size="sm"
            isIconOnly
            onPress={onToggleCollapsed}
            aria-label="Close sidebar"
            className="md:hidden text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X size={16} />
          </Button>
        </div>

        {/* New ticket button */}
        <div className="p-3">
          <Button fullWidth onPress={onNew} className="gap-2 bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 font-medium">
            <Plus size={16} />
            New ticket
          </Button>
        </div>

        <Separator className="mx-3 w-auto border-gray-100 dark:border-white/5" />

        {/* Conversation list */}
        <nav className="thin-scroll flex-1 overflow-y-auto px-2 py-3">
          {conversations.length === 0 && (
            <p className="px-2 py-6 text-center text-sm text-gray-400">No tickets yet.</p>
          )}
          <ul className="flex flex-col gap-0.5">
            {conversations.map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => handleSelect(c.id)}
                  className={
                    "group relative w-full truncate rounded-lg px-3 py-2.5 text-left text-sm transition-colors " +
                    (c.id === activeId
                      ? "bg-gray-100 font-semibold text-gray-900 dark:bg-[#2a2b2c] dark:text-gray-100"
                      : "text-gray-500 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-[#2a2b2c]/50 dark:hover:text-gray-200")
                  }
                  title={c.title}
                >
                  <span className="flex items-center gap-2">
                    <MessageSquare
                      size={13}
                      className={
                        c.id === activeId
                          ? "text-gray-700 dark:text-gray-300 shrink-0"
                          : "text-gray-300 shrink-0 group-hover:text-gray-400 dark:text-gray-600 dark:group-hover:text-gray-400"
                      }
                    />
                    <span className="truncate">{c.title || "Untitled ticket"}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      {/* Desktop collapse toggle button — hidden on mobile */}
      <Button
        variant="outline"
        size="sm"
        isIconOnly
        onPress={onToggleCollapsed}
        aria-label={collapsed ? "Show sidebar" : "Hide sidebar"}
        className={`
          absolute top-1/2 z-10 -translate-y-1/2
          hidden md:flex
          h-6 w-6 rounded-full border-gray-200
          bg-white shadow-md shadow-gray-100/50
          text-gray-500 hover:text-gray-900
          transition-all duration-300 hover:scale-110
          dark:border-white/10 dark:bg-[#1e1f20] dark:shadow-black/20 dark:text-gray-400 dark:hover:text-gray-100
          ${collapsed ? "left-2" : "left-[calc(18rem-0.75rem)]"}
        `}
      >
        {collapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
      </Button>
    </>
  );
}
