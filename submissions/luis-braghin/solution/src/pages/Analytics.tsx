import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ExecutiveTab from "@/components/analytics/ExecutiveTab";
import ChartsTab from "@/components/analytics/ChartsTab";

export default function Analytics() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Visão estratégica e análises detalhadas de performance</p>
      </div>

      <Tabs defaultValue="executive" className="space-y-6">
        <TabsList>
          <TabsTrigger value="executive">Executivo</TabsTrigger>
          <TabsTrigger value="charts">Análises</TabsTrigger>
        </TabsList>

        <TabsContent value="executive">
          <ExecutiveTab />
        </TabsContent>

        <TabsContent value="charts">
          <ChartsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
