import { EscolhaPerfil } from "@/components/EscolhaPerfil";
import { contagemPorVendedor, listarUsuarios } from "@/server/repositorio";
import { usuarioAtual } from "@/server/sessao";

export const metadata = { title: "Quem é você?" };

/** Só caminhos internos do app valem como destino depois da escolha. */
function destinoSeguro(voltar: string | undefined): string {
  return voltar && /^\/(painel|pipeline|leads)(\?[^\s]*)?$/.test(voltar) ? voltar : "/painel";
}

/** A raiz sempre mostra a entrada (O-37); com perfil na sessão, oferece "Continuar como <nome>". */
export default async function Pagina({ searchParams }: { searchParams: Promise<{ voltar?: string }> }) {
  const { voltar } = await searchParams;
  const destino = destinoSeguro(voltar);
  const [atual, usuarios, abertos] = await Promise.all([usuarioAtual(), listarUsuarios(), contagemPorVendedor()]);
  return (
    <EscolhaPerfil
      destino={destino}
      atual={atual ? { nome: atual.nome, papel: atual.papel } : null}
      usuarios={usuarios.map((u) => ({ ...u, abertos: u.vendedor ? (abertos.get(u.vendedor) ?? 0) : undefined }))}
    />
  );
}
