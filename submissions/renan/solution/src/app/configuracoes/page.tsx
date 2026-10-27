import type { Metadata } from "next";
import { SettingsForm } from "@/components/settings-form";
import { PageHeader } from "@/components/ui";

export const metadata: Metadata = { title: "Configurações" };

export default function SettingsPage() {
  return (
    <div className="max-w-[900px] space-y-8">
      <PageHeader
        title="Configurações"
        description="Conecte o Agente Gestor à API do Claude com a sua própria chave e escolha o modelo e o esforço de análise."
      />
      <SettingsForm />
    </div>
  );
}
