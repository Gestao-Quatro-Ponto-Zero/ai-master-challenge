import Link from "next/link";
import { Estado } from "@/components/Estado";
import { classeBotao } from "@/components/ui/Botao";

export default function NaoEncontrada() {
  return (
    <Estado titulo="Esta tela não existe" texto="O endereço pode ter mudado. Volte para o Painel e siga de lá.">
      <Link href="/painel" className={classeBotao("primario")}>
        Ir para o Painel
      </Link>
    </Estado>
  );
}
