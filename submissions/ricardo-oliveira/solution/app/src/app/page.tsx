import { redirect } from "next/navigation";
import { currentUser } from "@/lib/session";
import { getUsers } from "@/lib/data";
import { escolher } from "@/lib/actions";

export default async function Home() {
  const user = await currentUser();
  if (user) redirect(user.papel === "manager" ? "/manager" : "/meu-dia");
  const users = await getUsers();
  const reps = users.filter((u) => u.papel === "vendedor");
  const managers = users.filter((u) => u.papel === "manager");
  const teams = Array.from(new Set(reps.map((r) => r.manager)));
  return (
    <div className="grid md:grid-cols-2 gap-8 items-center py-8">
      <div>
        <h1 className="text-4xl font-extrabold leading-tight">
          Existe uma lista <span className="display-accent">pra cada vendedor</span>
        </h1>
        <p className="mt-4 text-base max-w-md">
          Abra na segunda e saiba onde focar. A ordem vem da planilha: deal vivo primeiro, conta na hora de recomprar, valor, ICP. Cada deal com o porquê e a próxima ação.
        </p>
        <ul className="mt-6 space-y-2 text-sm">
          <li><span className="tag tag-gold">1</span> Deal vivo em produto que a conta precisa recomprar agora</li>
          <li><span className="tag tag-gold">2</span> Os outros deals vivos</li>
          <li><span className="tag tag-gold">3</span> Deals antigos em conta na hora de recomprar</li>
          <li><span className="tag tag-gold">4</span> O resto</li>
          <li><span className="tag tag-navy">!</span> Confirmar: outro vendedor fechou o produto depois de o deal abrir. Mesmo pedido ou demanda separada? A conta responde, não o dado.</li>
        </ul>
      </div>
      <form action={escolher} className="card p-6 space-y-4">
        <h2 className="text-lg font-extrabold">Quem está olhando?</h2>
        <p className="text-sm text-grey">
          Na demo não tem login: escolha o vendedor ou o manager e veja a lista dele. Com a aprovação da RevOps, entra o login da empresa e cada um vê só o seu.
        </p>
        <label className="block text-sm font-semibold">
          Vendedor ou manager
          <select name="quem" required defaultValue="" className="mt-1 w-full border border-line rounded-lg px-3 py-2 bg-white">
            <option value="" disabled>Escolha…</option>
            {teams.map((t) => (
              <optgroup key={t} label={`Time ${t}`}>
                {reps.filter((r) => r.manager === t).map((r) => <option key={r.email} value={r.email}>{r.nome}</option>)}
              </optgroup>
            ))}
            <optgroup label="Managers">
              {managers.map((m) => <option key={m.email} value={m.email}>{m.nome} · manager</option>)}
            </optgroup>
          </select>
        </label>
        <button className="btn-primary w-full">Ver a lista</button>
        <p className="text-xs text-grey">{reps.length} vendedores em {teams.length} times, {managers.length} managers.</p>
      </form>
    </div>
  );
}
