import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { WelcomeModal } from "./components/WelcomeModal";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "G4 Lead Scorer",
  description: "Pipeline inteligente para equipes de vendas B2B · Powered by Lucas de Paula",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <WelcomeModal />
        {children}
      </body>
    </html>
  );
}
