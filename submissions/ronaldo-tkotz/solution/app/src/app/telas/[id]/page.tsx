import { notFound } from "next/navigation";
import { requireUser } from "@/app/lib/auth";
import { listarPaineis, listarPedidos, obterTela } from "@/engine/telasUsuario";
import { TelaShell } from "@/app/components/telas/TelaShell";
import { TelaPropria } from "@/app/components/telas/TelaPropria";

export const dynamic = "force-dynamic";

/** A screen the user built with the analyst (D46.2, ISC-41). */
export default async function TelaDoUsuario({ params }: { params: Promise<{ id: string }> }) {
  const user = await requireUser();
  const { id } = await params;
  const tela = obterTela(user.id, id);
  if (!tela) notFound();
  return (
    <TelaShell email={user.email} titulo={tela.nome} subtitulo="Sua tela: peça análises ao analista e os gráficos dele ficam aqui, com o SQL de cada um. Marque os que vão para a apresentação.">
      <TelaPropria tela={tela} pedidos={listarPedidos(user.id, id)} paineis={listarPaineis(user.id, id)} />
    </TelaShell>
  );
}
