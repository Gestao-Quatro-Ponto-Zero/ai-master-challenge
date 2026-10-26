import type { Metadata } from "next";
import { Manrope, Libre_Baskerville } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { currentUser } from "@/lib/session";
import { isLive } from "@/lib/data";

const manrope = Manrope({ variable: "--font-manrope", subsets: ["latin"], weight: ["200", "400", "600", "700", "800"] });
const baskerville = Libre_Baskerville({ variable: "--font-baskerville", subsets: ["latin"], weight: ["400"], style: ["italic", "normal"] });

export const metadata: Metadata = {
  title: "Lead Scorer · G4",
  description: "O vendedor abre na segunda e sabe onde focar.",
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const user = await currentUser();
  return (
    <html lang="pt-BR" className={`${manrope.variable} ${baskerville.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <Nav user={user} live={isLive()} />
        <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-6">{children}</main>
        <footer className="text-center text-xs text-grey py-6">
          Lead Scorer · Challenge 003 · a planilha é o motor, o app é a janela.
        </footer>
      </body>
    </html>
  );
}
