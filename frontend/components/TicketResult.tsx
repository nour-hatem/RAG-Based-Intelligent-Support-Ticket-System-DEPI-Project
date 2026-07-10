"use client";

import { useState } from "react";
import { Card, Chip, Alert, Button, Accordion } from "@heroui/react";
import { CheckCircle2, AlertTriangle, Copy, Layers } from "lucide-react";
import type { TicketResponse } from "@/lib/types";

interface TicketResultProps {
  result: TicketResponse;
}

function queueColor(queue: string): "success" | "danger" | "accent" | "default" {
  const q = queue.toLowerCase();
  if (q.includes("billing") || q.includes("payment")) return "success";
  if (q.includes("tech") || q.includes("it")) return "danger";
  return "accent";
}

export function TicketResult({ result }: TicketResultProps) {
  const [copied, setCopied] = useState(false);
  const confidencePct = Math.round((result.confidence_score ?? 0) * 100);

  function handleCopy() {
    if (!result.generated_answer) return;
    navigator.clipboard.writeText(result.generated_answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="flex flex-col gap-4">
      {result.needs_human_review && (
        <Alert status="danger">
          <Alert.Indicator>
            <AlertTriangle size={18} />
          </Alert.Indicator>
          <Alert.Content>
            <Alert.Title>Human attention required</Alert.Title>
            <Alert.Description>
              Confidence score is below threshold. Flagged for manual review.
            </Alert.Description>
          </Alert.Content>
        </Alert>
      )}

      {/* Classification + Confidence cards — 1-col on mobile, 2-col on sm+ */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card variant="default">
          <Card.Content className="flex flex-col gap-3 p-4 sm:p-5">
            <p className="flex items-center gap-1 text-xs font-bold uppercase tracking-wider text-muted">
              <Layers size={14} /> AI classification
            </p>
            <div>
              <span className="mb-1 block text-xs text-muted">Predicted queue</span>
              <Chip color={queueColor(result.predicted_queue)} variant="primary">
                <Chip.Label>{result.predicted_queue}</Chip.Label>
              </Chip>
            </div>
          </Card.Content>
        </Card>

        <Card variant="default">
          <Card.Content className="flex flex-col gap-2 p-4 sm:p-5">
            <p className="text-xs font-bold uppercase tracking-wider text-muted">Confidence</p>
            <span className="text-2xl font-black sm:text-3xl">{confidencePct}%</span>
            <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-default-200">
              <div
                className={`h-full rounded-full transition-all ${
                  confidencePct > 60 ? "bg-success" : "bg-warning"
                }`}
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </Card.Content>
        </Card>
      </div>

      <Card variant="default">
        <Card.Header className="flex flex-row items-center justify-between gap-2">
          <Card.Title className="flex items-center gap-2 text-sm">
            <CheckCircle2 size={18} className="text-success shrink-0" /> Generated draft reply
          </Card.Title>
          {result.generated_answer && (
            <Button
              size="sm"
              variant={copied ? "primary" : "outline"}
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
            <div className="min-h-[80px] whitespace-pre-wrap rounded-xl border border-default-200 bg-surface-secondary p-3 text-sm leading-relaxed sm:min-h-[100px] sm:p-4">
              {result.generated_answer}
            </div>
          ) : (
            <p className="text-sm italic text-muted">
              This ticket was routed to a human agent instead of an automated reply.
            </p>
          )}
        </Card.Content>
        <Card.Footer className="flex-col items-stretch gap-0 p-0">
          <Accordion className="w-full">
            <Accordion.Item id="details">
              <Accordion.Heading>
                <Accordion.Trigger className="px-4 py-2 text-xs text-muted">
                  Prediction details
                  <Accordion.Indicator />
                </Accordion.Trigger>
              </Accordion.Heading>
              <Accordion.Panel>
                <Accordion.Body className="flex flex-col gap-1.5 px-4 pb-4 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted">Predicted queue</span>
                    <span className="font-medium">{result.predicted_queue}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Confidence</span>
                    <span className="font-medium">{confidencePct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Needs human review</span>
                    <span className="font-medium">{result.needs_human_review ? "Yes" : "No"}</span>
                  </div>
                </Accordion.Body>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Card.Footer>
      </Card>
    </div>
  );
}
