import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "G4 Help",
  description: "Central de suporte inteligente com IA — G4 Educação",
  icons: {
    icon: [{ url: "/logo-g4.png", type: "image/png" }],
    shortcut: ["/logo-g4.png"],
    apple: ["/logo-g4.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="h-full">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
