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
      <Avatar size="sm" className="shrink-0 mt-5 bg-gradient-to-tr from-gray-800 to-gray-600 text-white shadow-sm">
        <Avatar.Fallback className="font-bold text-xs">AI</Avatar.Fallback>
      </Avatar>

      <div className="flex flex-col gap-3 max-w-[92%] sm:max-w-[85%] min-w-0">
        <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 px-1">Triage AI</span>

        {/* Human-review warning — neutral/amber tinted */}
        {result.needs_human_review && (
          <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/30 dark:bg-amber-950/20">
            <AlertTriangle size={16} className="mt-0.5 shrink-0 text-amber-600 dark:text-amber-500" />
            <div>
              <p className="text-sm font-semibold text-amber-800 dark:text-amber-200">Human attention required</p>
              <p className="mt-0.5 text-xs text-amber-700/80 dark:text-amber-400/80">
                Confidence score is below threshold. Flagged for manual review.
              </p>
            </div>
          </div>
        )}



        {/* Generated answer card */}
        <Card variant="default" className="border-gray-200 bg-white dark:border-white/10 dark:bg-[#1e1f20] shadow-sm">
          <Card.Header className="flex flex-row items-center justify-between gap-2 border-b border-gray-100 dark:border-white/5 pb-3">
            <Card.Title className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
              <CheckCircle2 size={16} className="shrink-0 text-gray-500 dark:text-gray-400" />
              Generated draft reply
            </Card.Title>
            {result.generated_answer && (
              <Button
                size="sm"
                variant={copied ? "secondary" : "ghost"}
                onPress={handleCopy}
                className="shrink-0 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              >
                <Copy size={14} />
                <span className="hidden xs:inline">{copied ? "Copied!" : "Copy"}</span>
              </Button>
            )}
          </Card.Header>

          <Card.Content className="pt-4">
            {result.generated_answer ? (
              <div className="min-h-[80px] rounded-xl border border-gray-100 bg-gray-50/50 p-3 dark:border-white/5 dark:bg-[#2a2b2c]/30 sm:min-h-[100px] sm:p-4">
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
                  <Accordion.Trigger className="px-4 py-2 text-xs text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200">
                    Prediction details
                    <Accordion.Indicator />
                  </Accordion.Trigger>
                </Accordion.Heading>
                <Accordion.Panel>
                  <Accordion.Body className="flex flex-col gap-1.5 px-4 pb-4 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Predicted queue</span>
                      <span className="font-medium text-gray-800 dark:text-gray-200">{result.predicted_queue}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Confidence</span>
                      <span className="font-medium text-gray-800 dark:text-gray-200">{confidencePct}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Needs human review</span>
                      <span className="font-medium text-gray-800 dark:text-gray-200">
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
