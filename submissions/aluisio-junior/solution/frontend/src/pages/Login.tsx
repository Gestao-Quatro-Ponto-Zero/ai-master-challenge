import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Activity, Loader2 } from "lucide-react";

const Login = () => {
  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);

    if (isSignUp) {
      const { error: err } = await signup(email, password);
      if (err) {
        setError(err);
      } else {
        setInfo("Conta criada! Verifique seu email para confirmar o cadastro.");
      }
    } else {
      const { error: err } = await login(email, password);
      if (err) {
        setError("Credenciais inválidas");
      } else {
        navigate("/");
      }
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm animate-fade-in">
        <div className="flex items-center justify-center gap-2 mb-8">
          <Activity className="h-8 w-8 text-primary" />
          <h1 className="text-2xl font-bold tracking-tight">Churn Intelligence</h1>
        </div>

        <div className="glass-card p-8">
          <h2 className="text-lg font-semibold mb-1">
            {isSignUp ? "Criar Conta" : "Entrar"}
          </h2>
          <p className="text-sm text-muted-foreground mb-6">
            {isSignUp
              ? "Cadastre-se para acessar o painel"
              : "Acesse o painel de análise de churn"}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
            {info && <p className="text-sm text-primary">{info}</p>}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isSignUp ? "Cadastrar" : "Entrar"}
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t border-border">
            <p className="text-xs text-muted-foreground text-center">
              {isSignUp ? "Já tem conta?" : "Não tem conta?"}{" "}
              <button
                type="button"
                className="text-primary hover:underline font-medium"
                onClick={() => {
                  setIsSignUp(!isSignUp);
                  setError("");
                  setInfo("");
                }}
              >
                {isSignUp ? "Entrar" : "Cadastrar"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
