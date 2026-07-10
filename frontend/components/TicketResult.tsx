"use client";

import { useState } from "react";
import { Card, Chip, Avatar, Accordion } from "@heroui/react";
import { Button } from "@heroui/react";
import { CheckCircle2, AlertTriangle, Copy, Layers, Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { TicketResponse } from "@/lib/types";

interface TicketResultProps {
  result: TicketResponse;
  createdAt?: number;
}

export function TicketResult({ result, createdAt }: TicketResultProps) {
  const [copied, setCopied] = useState(false);
  const confidencePct = Math.round((result.confidence_score ?? 0) * 100);

  const time = createdAt
    ? new Date(createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : null;

  function handleCopy() {
    if (!result.generated_answer) return;
    navigator.clipboard.writeText(result.generated_answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="message-enter flex justify-start items-start gap-2.5">
      {/* Bot avatar */}
      <Avatar size="sm" variant="soft" color="default" className="shrink-0 mt-5">
        <Avatar.Fallback className="text-blue-600 font-bold text-xs">AI</Avatar.Fallback>
      </Avatar>

      <div className="flex flex-col gap-3 max-w-[92%] sm:max-w-[85%] min-w-0">
        <span className="text-xs font-semibold text-blue-500 px-1">Triage AI</span>

        {/* Human-review warning — blue-tinted, not red */}
        {result.needs_human_review && (
          <div className="flex items-start gap-3 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 dark:border-blue-800/40 dark:bg-blue-950/30">
            <AlertTriangle size={16} className="mt-0.5 shrink-0 text-blue-500" />
            <div>
              <p className="text-sm font-semibold text-blue-800 dark:text-blue-200">Human attention required</p>
              <p className="mt-0.5 text-xs text-blue-700/80 dark:text-blue-300/70">
                Confidence score is below threshold. Flagged for manual review.
              </p>
            </div>
          </div>
        )}

        {/* Classification + Confidence — 1-col on mobile, 2-col on sm+ */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {/* Classification */}
          <Card variant="default">
            <Card.Content className="flex flex-col gap-3 p-4 sm:p-5">
              <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-blue-500/80">
                <Layers size={13} />
                AI Classification
              </p>
              <div>
                <span className="mb-1.5 block text-xs text-gray-500 dark:text-gray-400">Predicted queue</span>
                {/* Blue-only chip — no color prop that maps to red/purple */}
                <Chip
                  variant="soft"
                  color="default"
                  size="sm"
                  className="border border-blue-200 bg-blue-50 dark:border-blue-800/40 dark:bg-blue-950/30"
                >
                  <Chip.Label className="font-semibold text-blue-700 dark:text-blue-300">
                    {result.predicted_queue}
                  </Chip.Label>
                </Chip>
              </div>
            </Card.Content>
          </Card>

          {/* Confidence */}
          <Card variant="default">
            <Card.Content className="flex flex-col gap-2 p-4 sm:p-5">
              <p className="text-xs font-bold uppercase tracking-wider text-blue-500/80">Confidence</p>
              <span className="text-2xl font-black text-blue-700 dark:text-blue-300 sm:text-3xl">
                {confidencePct}%
              </span>
              {/* Blue-only progress bar */}
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-blue-100 dark:bg-blue-900/40">
                <div
                  className="h-full rounded-full bg-blue-500 transition-all duration-700"
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
            </Card.Content>
          </Card>
        </div>

        {/* Generated answer card */}
        <Card variant="default">
          <Card.Header className="flex flex-row items-center justify-between gap-2">
            <Card.Title className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
              <CheckCircle2 size={16} className="shrink-0 text-blue-500" />
              Generated draft reply
            </Card.Title>
            {result.generated_answer && (
              <Button
                size="sm"
                variant={copied ? "secondary" : "ghost"}
                onPress={handleCopy}
                className="shrink-0"
              >
                <Copy size={14} />
                <span className="hidden xs:inline">{copied ? "Copied!" : "Copy"}</span>
              </Button>
            )}
          </Card.Header>

          <Card.Content>
            {result.generated_answer ? (
              <div className="min-h-[80px] rounded-xl border border-blue-100 bg-blue-50/40 p-3 dark:border-blue-900/30 dark:bg-blue-950/20 sm:min-h-[100px] sm:p-4">
                {/* Markdown rendering for RAG responses */}
                <div className="markdown-body text-gray-800 dark:text-gray-200">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {result.generated_answer}
                  </ReactMarkdown>
                </div>
              </div>
            ) : (
              <p className="text-sm italic text-gray-500 dark:text-gray-400">
                This ticket was routed to a human agent instead of an automated reply.
              </p>
            )}
          </Card.Content>

          <Card.Footer className="flex-col items-stretch gap-0 p-0">
            <Accordion className="w-full">
              <Accordion.Item id="details">
                <Accordion.Heading>
                  <Accordion.Trigger className="px-4 py-2 text-xs text-gray-500 hover:text-blue-600 dark:text-gray-400">
                    Prediction details
                    <Accordion.Indicator />
                  </Accordion.Trigger>
                </Accordion.Heading>
                <Accordion.Panel>
                  <Accordion.Body className="flex flex-col gap-1.5 px-4 pb-4 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Predicted queue</span>
                      <span className="font-medium text-blue-700 dark:text-blue-300">{result.predicted_queue}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Confidence</span>
                      <span className="font-medium text-blue-700 dark:text-blue-300">{confidencePct}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Needs human review</span>
                      <span className="font-medium text-blue-700 dark:text-blue-300">
                        {result.needs_human_review ? "Yes" : "No"}
                      </span>
                    </div>
                  </Accordion.Body>
                </Accordion.Panel>
              </Accordion.Item>
            </Accordion>
          </Card.Footer>
        </Card>

        {time && (
          <span className="text-[10px] text-gray-400 px-1 select-none">{time}</span>
        )}
      </div>
    </div>
  );
}
