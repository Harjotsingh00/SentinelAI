import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelAI — Emergency Intelligence Platform",
  description:
    "AI-powered multi-agent emergency intelligence platform for real-time incident analysis, resource allocation, and public communication.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
