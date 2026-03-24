import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";

export default function NotFound() {
  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background">
      <Card className="w-full max-w-md mx-4">
        <CardContent className="pt-6 pb-8 text-center">
          <div className="flex justify-center mb-4">
            <AlertCircle className="h-12 w-12 text-destructive" />
          </div>
          <h1 className="text-2xl font-display font-bold text-foreground mb-2">Página não encontrada</h1>
          <p className="text-muted-foreground mb-6">A página que você está procurando não existe.</p>
          <Link href="/">
            <Button data-testid="button-go-home">Voltar ao início</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
