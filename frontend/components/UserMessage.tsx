"use client";

import { Avatar } from "@heroui/react";

interface UserMessageProps {
  subject?: string;
  text: string;
  createdAt?: number;
}

export function UserMessage({ subject, text, createdAt }: UserMessageProps) {
  const time = createdAt
    ? new Date(createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <div className="message-enter flex justify-end items-end gap-2.5">
      {/* Bubble */}
      <div className="flex flex-col items-end gap-1 max-w-[82%] sm:max-w-[70%]">
        {subject && (
          <span className="text-xs text-gray-500 font-medium px-1">
            {subject}
          </span>
        )}
        <div className="bg-gray-100 text-gray-900 dark:bg-[#1e1f20] dark:text-gray-100 rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm border border-transparent dark:border-white/5">
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{text}</p>
        </div>
        {time && (
          <span className="text-[10px] text-gray-400 px-1 select-none">{time}</span>
        )}
      </div>

      {/* Avatar */}
      <Avatar size="sm" className="shrink-0 mb-5 bg-gray-200 text-gray-600 dark:bg-[#2a2b2c] dark:text-gray-400">
        <Avatar.Fallback>U</Avatar.Fallback>
      </Avatar>
    </div>
  );
}
