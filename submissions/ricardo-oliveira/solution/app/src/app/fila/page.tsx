import { redirect } from "next/navigation";
import { currentUser } from "@/lib/session";
import { getRep } from "@/lib/data";
import { F } from "@/lib/types";
import { str, usd, dateBR } from "@/lib/parse";

export default async function Fila() {
  const user = await currentUser();
  if (!user) redirect("/");
  const d = await getRep(user.email);
  if (!d) redirect("/");
  const fora = d.fila.filter((f) => str(f[F.escalada]) === "Escalar pro manager").length;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-extrabold">Fila <span className="display-accent">sem conta</span></h1>
      <p className="text-sm max-w-2xl">
        {d.fila.length} deals seus estão no CRM sem conta. Eles não entram na lista do dia até a conta ser identificada.
        É tarefa de todo dia, depois dos deals vivos: vivos primeiro, depois pelo preço. Prazo {str(d.config.prazoFilaDiasUteis)} dias úteis;
        {fora ? ` ${fora} já passaram do prazo e escalam pro manager.` : " nenhum passou do prazo ainda."}
        {" "}Quando identificar, marque na planilha (coluna Status) ou peça pro manager.
      </p>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-navy text-offwhite text-left">
            <tr>
              <th className="p-2">#</th><th className="p-2">Oportunidade</th><th className="p-2">Produto</th><th className="p-2">Preço</th>
              <th className="p-2">Estágio</th><th className="p-2">Dias aberto</th><th className="p-2">Vivo?</th><th className="p-2">Prazo</th><th className="p-2">Escalada</th>
            </tr>
          </thead>
          <tbody>
            {d.fila.map((f) => (
              <tr key={str(f[F.id])} className="border-t border-line">
                <td className="p-2 font-bold text-gold-dark">{str(f[F.ordem])}</td>
                <td className="p-2">{str(f[F.id])}</td>
                <td className="p-2">{str(f[F.produto])}</td>
                <td className="p-2">{usd(f[F.preco])}</td>
                <td className="p-2">{str(f[F.estagio])}</td>
                <td className="p-2">{str(f[F.diasAberto])}</td>
                <td className="p-2"><span className={`tag ${str(f[F.vivo]) === "Vivo" ? "tag-ok" : "tag-navy"}`}>{str(f[F.vivo])}</span></td>
                <td className="p-2">{dateBR(f[F.prazo])}</td>
                <td className="p-2"><span className={`tag ${str(f[F.escalada]) === "Escalar pro manager" ? "tag-bad" : "tag-navy"}`}>{str(f[F.escalada])}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
