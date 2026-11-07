import "./globals.css";
export const metadata = {
  title: "G4 Sales Priority | Meu dia",
  description:
    "Prioridades explicáveis, próximas ações e pipeline comercial em movimento.",
};
export default function Layout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
