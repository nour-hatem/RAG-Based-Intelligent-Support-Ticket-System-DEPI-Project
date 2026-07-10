"use client";

import { Card, Skeleton } from "@heroui/react";

export function ThinkingBubble() {
  return (
    <div className="flex justify-start">
      <Card variant="default" className="w-full max-w-[85%] sm:w-[80%] sm:max-w-md">
        <Card.Header>
          <Card.Title className="text-sm text-muted">Triage AI</Card.Title>
          <Card.Description>Thinking…</Card.Description>
        </Card.Header>
        <Card.Content className="flex flex-col gap-2">
          <Skeleton className="h-3 w-3/4 rounded-md" />
          <Skeleton className="h-3 w-full rounded-md" />
          <Skeleton className="h-3 w-5/6 rounded-md" />
        </Card.Content>
      </Card>
    </div>
  );
}
