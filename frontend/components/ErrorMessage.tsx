"use client";

import { Alert } from "@heroui/react";

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="flex justify-start">
      <Alert status="danger" className="max-w-[80%]">
        <Alert.Indicator />
        <Alert.Content>
          <Alert.Title>Something went wrong</Alert.Title>
          <Alert.Description>{message}</Alert.Description>
        </Alert.Content>
      </Alert>
    </div>
  );
}
