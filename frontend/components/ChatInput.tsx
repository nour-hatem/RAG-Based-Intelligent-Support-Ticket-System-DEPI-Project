"use client";

import { useState } from "react";
import { Button, Spinner } from "@heroui/react";
import { TextField, Input, TextArea, Label, Description } from "@heroui/react";
import { Send } from "lucide-react";

interface ChatInputProps {
  onSubmit: (subject: string, body: string) => void;
  isSending: boolean;
}

const MAX_BODY_LENGTH = 5000;

export function ChatInput({ onSubmit, isSending }: ChatInputProps) {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = body.trim();
    if (!trimmed) {
      setError("Message is required.");
      return;
    }
    if (trimmed.length > MAX_BODY_LENGTH) {
      setError(`Message exceeds ${MAX_BODY_LENGTH} characters.`);
      return;
    }
    setError("");
    onSubmit(subject.trim(), trimmed);
    setSubject("");
    setBody("");
  }

  const charPct = Math.round((body.length / MAX_BODY_LENGTH) * 100);
  const charColor =
    charPct > 90 ? "text-red-500" : charPct > 70 ? "text-yellow-500" : "text-gray-400";

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 border-t border-blue-100 bg-white/80 p-3 backdrop-blur-sm dark:border-blue-900/30 dark:bg-gray-950/80 sm:p-4"
    >
      {/* Thinking indicator — shown above input while AI responds */}
      {isSending && (
        <div className="flex items-center gap-2 rounded-lg border border-blue-100 bg-blue-50/60 px-3 py-2 dark:border-blue-900/30 dark:bg-blue-950/30">
          <Spinner size="sm" color="current" />
          <span className="text-xs text-blue-600 dark:text-blue-400">AI is thinking…</span>
          <span className="flex items-center gap-1 ml-auto">
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-blue-400" />
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-blue-400" />
            <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-blue-400" />
          </span>
        </div>
      )}

      {/* Subject field */}
      <TextField
        value={subject}
        onChange={setSubject}
        isDisabled={isSending}
        className="flex flex-col gap-1"
      >
        <Label className="text-xs font-medium text-blue-600/80 dark:text-blue-400/80">
          Subject <span className="text-gray-400 font-normal">(optional)</span>
        </Label>
        <Input
          fullWidth
          placeholder="e.g. Refund not received"
          className="rounded-lg border-blue-200 focus:border-blue-500 dark:border-blue-800/50"
        />
      </TextField>

      {/* Message row */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <TextField
          value={body}
          onChange={setBody}
          isDisabled={isSending}
          isRequired
          className="flex flex-1 flex-col gap-1"
        >
          <Label className="text-xs font-medium text-blue-600/80 dark:text-blue-400/80">
            Message
          </Label>
          <TextArea
            fullWidth
            placeholder="Type the customer's message here…"
            maxLength={MAX_BODY_LENGTH}
            rows={3}
            className="rounded-lg border-blue-200 focus:border-blue-500 dark:border-blue-800/50"
          />
          <Description>
            <span className={`text-xs tabular-nums transition-colors ${charColor}`}>
              {body.length.toLocaleString()} / {MAX_BODY_LENGTH.toLocaleString()}
            </span>
          </Description>
        </TextField>

        {/* Send button */}
        <Button
          type="submit"
          variant="primary"
          isDisabled={isSending || !body.trim()}
          aria-busy={isSending}
          className="shrink-0 gap-2 sm:self-end"
        >
          {isSending ? (
            <>
              <Spinner size="sm" color="current" />
              <span className="hidden sm:inline">Analyzing…</span>
            </>
          ) : (
            <>
              <Send size={16} />
              <span className="hidden xs:inline">Send</span>
            </>
          )}
        </Button>
      </div>

      {error && (
        <span className="text-xs text-red-500 font-medium">{error}</span>
      )}
    </form>
  );
}
