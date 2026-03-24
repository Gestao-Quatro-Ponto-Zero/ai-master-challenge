import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ShieldCheck } from "lucide-react";
import { Link } from "wouter";
import { useAuth } from "@/context/auth";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("admin@hermes.io");
  const [password, setPassword] = useState("hermes123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const userData = await login(email, password);
      window.location.href = userData.role === "admin" ? "/admin" : "/meus-chamados";
    } catch (err: any) {
      setError(err.message || "Erro ao fazer login");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] bg-primary/5 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] bg-secondary/5 rounded-full blur-[120px] pointer-events-none"></div>

      <Card className="w-full max-w-md relative z-10 border-border shadow-lg">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-secondary via-primary to-secondary rounded-t-lg"></div>
        <CardHeader className="text-center pt-10 pb-6">
          <div className="mx-auto w-16 h-16 bg-secondary rounded-lg flex items-center justify-center mb-6 shadow-md">
            <ShieldCheck className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2" data-testid="text-app-name">Hermes</h1>
          <p className="text-sm text-muted-foreground tracking-widest uppercase font-semibold">Suporte de TI com IA</p>
        </CardHeader>
        <CardContent className="px-10 pb-10">
          <form onSubmit={handleLogin} className="space-y-6">
            {error && (
              <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-lg border border-destructive/20" data-testid="text-login-error">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">E-mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="h-12 border-border bg-background focus-visible:ring-primary focus-visible:border-primary"
                data-testid="input-email"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Senha</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="h-12 border-border bg-background focus-visible:ring-primary focus-visible:border-primary"
                data-testid="input-password"
                required
              />
            </div>
            <Button type="submit" className="w-full h-12 font-semibold tracking-wide rounded-lg" disabled={loading} data-testid="button-login">
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
          <p className="text-center text-sm text-muted-foreground mt-6">
            Não tem conta?{" "}
            <Link href="/cadastro" className="text-primary font-semibold hover:underline" data-testid="link-register">Cadastre-se</Link>
          </p>
          <div className="mt-6 pt-4 border-t border-border text-xs text-muted-foreground space-y-1">
            <p className="font-semibold text-center mb-2">Credenciais de teste:</p>
            <p>Admin: <span className="font-mono">admin@hermes.io</span> / <span className="font-mono">hermes123</span></p>
            <p>Usuário: <span className="font-mono">joao@empresa.com</span> / <span className="font-mono">senha123</span></p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
