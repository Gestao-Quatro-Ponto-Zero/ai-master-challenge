import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Veta — the analyst that finds what you'd miss",
  description:
    "Diagnóstico de churn da RavenStack. Cada número vem de uma consulta SQL que você pode inspecionar.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
