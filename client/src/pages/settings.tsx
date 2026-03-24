import { AppLayout } from "@/components/layout/app-layout";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

export default function Settings() {
  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2" data-testid="text-page-title">Configurações do Sistema</h1>
          <p className="text-muted-foreground text-lg">Gerencie o comportamento do Hermes IA e regras operacionais.</p>
        </div>

        <Card className="mb-6 border-border">
          <CardHeader>
            <CardTitle className="text-xl text-foreground">Regras de Automação IA</CardTitle>
            <CardDescription>Controle como a IA interage automaticamente com os chamados recebidos.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Classificação Automática</Label>
                <p className="text-sm text-muted-foreground">Atribuir categoria e prioridade automaticamente com base em análise de texto.</p>
              </div>
              <Switch defaultChecked data-testid="switch-auto-classification" />
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Roteamento Automático</Label>
                <p className="text-sm text-muted-foreground">Encaminhar chamados diretamente para equipes com base na classificação.</p>
              </div>
              <Switch defaultChecked data-testid="switch-auto-routing" />
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Resposta Automática (Alta Confiança)</Label>
                <p className="text-sm text-muted-foreground">Permitir que a IA responda diretamente quando a confiança for superior a 95%.</p>
              </div>
              <Switch data-testid="switch-auto-response" />
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <div className="space-y-0.5">
                <Label className="text-base font-semibold">Notificações por E-mail</Label>
                <p className="text-sm text-muted-foreground">Enviar e-mails automáticos ao atualizar o status de um chamado.</p>
              </div>
              <Switch defaultChecked data-testid="switch-email-notifications" />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-4">
          <Button variant="outline" className="rounded-lg" data-testid="button-discard-settings">Descartar Alterações</Button>
          <Button className="rounded-lg" data-testid="button-save-settings">Salvar Configurações</Button>
        </div>
      </div>
    </AppLayout>
  );
}
