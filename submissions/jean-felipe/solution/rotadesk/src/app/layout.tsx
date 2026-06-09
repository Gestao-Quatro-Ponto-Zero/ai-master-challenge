import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RotaDesk — Suporte inteligente",
  description: "Protótipo Challenge 002 — triagem, ack e atendimento com IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="h-full">
      <body className="min-h-full antialiased">{children}</body>
    </html>
  );
}
