import Link from "next/link";
import { Estado } from "@/components/Estado";

export default function NaoEncontrada() {
  return (
    <Estado titulo="Esta tela não existe" texto="O endereço pode ter mudado. Volte para o Painel e siga de lá.">
      <Link href="/painel" className="rounded-controle bg-marinho px-4 py-2 text-sm font-semibold text-branco">
        Ir para o Painel
      </Link>
    </Estado>
  );
}
