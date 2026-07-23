"use client";
import { ErrorState } from "@/components/ui";
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) { return <ErrorState title="Não foi possível carregar esta seção" message="Um artefato local obrigatório está ausente ou inválido." action={reset} />; }
