"use client";

import { Card } from "@heroui/react";

interface UserMessageProps {
  subject?: string;
  text: string;
}

export function UserMessage({ subject, text }: UserMessageProps) {
  return (
    <div className="flex justify-end">
      <Card variant="secondary" className="w-full max-w-[85%] sm:max-w-[75%]">
        <Card.Header>
          <Card.Title className="text-sm text-muted">You</Card.Title>
          {subject && <Card.Description>{subject}</Card.Description>}
        </Card.Header>
        <Card.Content>
          <p className="whitespace-pre-wrap text-sm">{text}</p>
        </Card.Content>
      </Card>
    </div>
  );
}
