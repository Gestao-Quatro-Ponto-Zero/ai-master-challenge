import Link from "next/link";

export default function DealNotFound() {
  return (
    <div>
      <h1 className="text-[clamp(30px,4vw,56px)] font-semibold tracking-[-0.03em]">Deal não encontrado</h1>
      <p className="mt-3 text-[17px] text-secondary">O código não existe no pipeline aberto. Ele pode ter sido fechado ou digitado errado.</p>
      <p className="mt-6">
        <Link href="/pipeline" className="link text-[17px]">
          Buscar no pipeline
        </Link>
      </p>
    </div>
  );
}
