"use client";

import { Alert, Avatar } from "@heroui/react";
import { AlertTriangle } from "lucide-react";

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="message-enter flex justify-start items-end gap-2.5">
      {/* Bot avatar */}
      <Avatar size="sm" variant="soft" color="default" className="shrink-0 mb-1">
        <Avatar.Fallback className="text-blue-600 font-bold text-xs">AI</Avatar.Fallback>
      </Avatar>

      <div className="flex flex-col gap-1 max-w-[85%] sm:max-w-[80%]">
        <span className="text-xs font-semibold text-blue-500 px-1">Triage AI</span>
        {/* Blue-tinted alert — not red */}
        <div className="flex items-start gap-3 rounded-2xl rounded-tl-sm border border-blue-200 bg-blue-50 px-4 py-3 shadow-sm dark:border-blue-800/40 dark:bg-blue-950/30">
          <AlertTriangle size={16} className="mt-0.5 shrink-0 text-blue-400" />
          <div>
            <p className="text-sm font-semibold text-blue-800 dark:text-blue-200">Something went wrong</p>
            <p className="mt-0.5 text-xs text-blue-700/80 dark:text-blue-300/70">{message}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
