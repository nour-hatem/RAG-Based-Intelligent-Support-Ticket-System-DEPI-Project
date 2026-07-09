"use client";

import { Card, Accordion } from "@heroui/react";
import type { TicketResponse } from "@/lib/types";

interface TicketResultProps {
  result: TicketResponse;
}

export function TicketResult({ result }: TicketResultProps) {
  const confidencePct = Math.round((result.confidence_score ?? 0) * 100);

  return (
    <div className="flex justify-start">
      <Card variant="default" className="max-w-[80%]">
        <Card.Header>
          <Card.Title className="text-sm text-muted">Triage AI</Card.Title>
          {/* This is the "Source/Reference" the compound header shows —
              the predicted queue is the only retrieval-derived signal
              this backend exposes to the client. */}
          <Card.Description>
            Routed to: <span className="font-medium text-foreground">{result.predicted_queue}</span>
          </Card.Description>
        </Card.Header>

        <Card.Content>
          {result.generated_answer ? (
            <p className="whitespace-pre-wrap text-sm">{result.generated_answer}</p>
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
