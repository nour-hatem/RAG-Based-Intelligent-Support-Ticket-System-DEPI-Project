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
          border-r border-blue-100 bg-white
          transition-all duration-300 ease-in-out
          dark:border-blue-900/30 dark:bg-gray-950
          md:relative md:z-auto md:inset-auto md:h-full
          ${
            collapsed
              ? "-translate-x-full md:translate-x-0 md:w-0 md:overflow-hidden md:opacity-0 md:border-0"
              : "translate-x-0 w-72 opacity-100"
          }
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between gap-2 border-b border-blue-100 p-4 dark:border-blue-900/30">
          <div>
            <p className="font-bold leading-tight text-blue-700 dark:text-blue-300">Triage</p>
            <p className="text-xs text-gray-400">Ticket routing history</p>
          </div>
          {/* Close button — visible only on mobile */}
          <Button
            variant="ghost"
            size="sm"
            isIconOnly
            onPress={onToggleCollapsed}
            aria-label="Close sidebar"
            className="md:hidden text-gray-400 hover:text-blue-600"
          >
            <X size={16} />
          </Button>
        </div>

        {/* New ticket button */}
        <div className="p-3">
          <Button variant="primary" fullWidth onPress={onNew} className="gap-2">
            <Plus size={16} />
            New ticket
          </Button>
        </div>

        <Separator className="mx-3 w-auto border-blue-100 dark:border-blue-900/30" />

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
                      ? "border-l-2 border-blue-500 bg-blue-50 pl-2.5 font-semibold text-blue-700 dark:bg-blue-950/40 dark:text-blue-300"
                      : "border-l-2 border-transparent pl-2.5 text-gray-500 hover:bg-blue-50/60 hover:text-blue-600 dark:text-gray-400 dark:hover:bg-blue-950/20 dark:hover:text-blue-400")
                  }
                  title={c.title}
                >
                  <span className="flex items-center gap-2">
                    <MessageSquare
                      size={13}
                      className={
                        c.id === activeId
                          ? "text-blue-500 shrink-0"
                          : "text-gray-300 shrink-0 group-hover:text-blue-400"
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
          h-6 w-6 rounded-full border-blue-200
          bg-white shadow-md shadow-blue-100/50
          text-blue-500 hover:text-blue-700
          transition-all duration-300 hover:scale-110
          dark:border-blue-800/40 dark:bg-gray-900 dark:shadow-blue-900/20
          ${collapsed ? "left-2" : "left-[calc(18rem-0.75rem)]"}
        `}
      >
        {collapsed ? <ChevronRight size={13} /> : <ChevronLeft size={13} />}
      </Button>
    </>
  );
}
