"use client";

import { useState } from "react";
import { Button, TextField, Input, TextArea, Label, Description } from "@heroui/react";
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

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 border-t border-default-200 p-3 sm:p-4"
    >
      <TextField
        value={subject}
        onChange={setSubject}
        isDisabled={isSending}
        className="flex flex-col gap-1"
      >
        <Label className="text-xs text-muted">Subject (optional)</Label>
        <Input fullWidth placeholder="e.g. Refund not received" />
      </TextField>

      {/* Message row — stacks vertically on very small screens */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
        <TextField
          value={body}
          onChange={setBody}
          isDisabled={isSending}
          isRequired
          className="flex flex-1 flex-col gap-1"
        >
          <Label className="text-xs text-muted">Message</Label>
          <TextArea
            fullWidth
            placeholder="Type the customer's message here…"
            maxLength={MAX_BODY_LENGTH}
            rows={2}
          />
          <Description className="text-xs text-muted">
            {body.length} / {MAX_BODY_LENGTH}
          </Description>
        </TextField>

        <Button
          type="submit"
          variant="primary"
          isDisabled={isSending || !body.trim()}
          className="shrink-0 sm:self-end"
        >
          <Send size={16} />
          <span className="hidden xs:inline">
            {isSending ? "Analyzing…" : "Send"}
          </span>
          <span className="xs:hidden">{isSending ? "…" : "Send"}</span>
        </Button>
      </div>

      {error && <span className="text-xs text-danger">{error}</span>}
    </form>
  );
}
