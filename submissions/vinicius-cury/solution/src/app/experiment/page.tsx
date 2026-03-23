import { PageHeader } from "@/components/page-header";
import { ExperimentView } from "./experiment-view";

export default function ExperimentPage() {
  return (
    <>
      <PageHeader
        title="Experimento: Sub-classificação Zero-Shot"
        description="Avaliação manual da sub-classificação D2→D1. Classifique cada resultado como correto, errado ou parcial."
      />
      <ExperimentView />
    </>
  );
}
