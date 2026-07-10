"use client";

import { Avatar, Spinner } from "@heroui/react";

export function ThinkingBubble() {
  return (
    <div className="message-enter flex justify-start items-end gap-2.5">
      {/* Bot avatar */}
      <Avatar size="sm" variant="soft" color="accent" className="shrink-0 mb-1 !bg-blue-100 dark:!bg-blue-900/40">
        <Avatar.Fallback className="text-blue-600 font-bold text-xs">AI</Avatar.Fallback>
      </Avatar>

      {/* Bubble */}
      <div className="flex flex-col gap-1 max-w-[75%] sm:max-w-md">
        <span className="text-xs font-semibold text-blue-500 px-1">Triage AI</span>
        <div className="flex items-center gap-3 rounded-2xl rounded-tl-sm border border-blue-100 bg-blue-50/60 px-4 py-3 shadow-sm dark:border-blue-900/40 dark:bg-blue-950/30">
          <Spinner size="sm" color="current" />
          <span className="text-sm text-gray-500 dark:text-gray-400">Analyzing your ticket…</span>
          {/* Animated dots */}
          <span className="flex items-center gap-1 ml-auto">
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-blue-400" />
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-blue-400" />
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-blue-400" />
          </span>
        </div>
      </div>
    </div>
  );
}
