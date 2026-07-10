import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Triage — Intelligent Ticket Routing",
  description: "RAG-powered support ticket triage",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="light" data-theme="light" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
