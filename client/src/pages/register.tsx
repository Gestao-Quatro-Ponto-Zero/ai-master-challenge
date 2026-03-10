import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ShieldCheck } from "lucide-react";
import { Link, useLocation } from "wouter";
import { useAuth } from "@/context/auth";

export default function Register() {
  const [, setLocation] = useLocation();
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await register(name, email, password);
      setLocation(user.role === "admin" ? "/admin" : "/meus-chamados");
    } catch (err: any) {
      setError(err.message || "Erro ao cadastrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-full greek-pattern-bg opacity-30 pointer-events-none"></div>
      <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/10 rounded-full blur-[120px] pointer-events-none"></div>

      <Card className="w-full max-w-md relative z-10 border-secondary/20">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-secondary to-primary rounded-t-md"></div>
        <CardHeader className="text-center pt-10 pb-6">
          <div className="mx-auto w-16 h-16 bg-primary rounded-md flex items-center justify-center mb-6 shadow-lg shadow-primary/20 transform -rotate-3">
            <ShieldCheck className="w-8 h-8 text-secondary transform rotate-3" />
          </div>
          <h1 className="text-4xl font-display font-bold text-foreground mb-2">Hermes</h1>
          <p className="text-sm text-muted-foreground tracking-widest uppercase font-semibold">Criar conta</p>
        </CardHeader>
        <CardContent className="px-10 pb-10">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md border border-destructive/20" data-testid="text-register-error">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Nome completo</Label>
              <Input id="name" value={name} onChange={e => setName(e.target.value)} placeholder="Seu nome" className="h-12 border-border/50 bg-background/50" required data-testid="input-name" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">E-mail</Label>
              <Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="seu@email.com" className="h-12 border-border/50 bg-background/50" required data-testid="input-email" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Senha</Label>
              <Input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Mínimo 6 caracteres" className="h-12 border-border/50 bg-background/50" required data-testid="input-password" />
            </div>
            <Button type="submit" className="w-full h-12 font-semibold tracking-wide" disabled={loading} data-testid="button-register">
              {loading ? "Cadastrando..." : "Criar conta"}
            </Button>
          </form>
          <p className="text-center text-sm text-muted-foreground mt-6">
            Já tem conta?{" "}
            <Link href="/entrar" className="text-secondary font-semibold" data-testid="link-login">Entrar</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
