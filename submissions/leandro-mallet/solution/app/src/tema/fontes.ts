import { Libre_Baskerville, Manrope } from "next/font/google";

// Servidas pelo próprio app (next/font baixa no build), sem pedido externo no navegador.
export const libreBaskerville = Libre_Baskerville({
  subsets: ["latin"],
  weight: ["400", "700"],
  display: "swap",
  variable: "--fonte-libre-baskerville",
});

export const manrope = Manrope({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--fonte-manrope",
});
