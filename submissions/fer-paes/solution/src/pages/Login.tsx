import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, AlertCircle, Zap } from 'lucide-react';
import { login } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const { setAuth } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('E-mail é obrigatório.');
      return;
    }
    if (!password) {
      setError('Senha é obrigatória.');
      return;
    }

    setIsLoading(true);
    try {
      const payload = await login({ email, password });
      setAuth({
        user: payload.user,
        profile: payload.profile,
        roles: payload.roles,
        permissions: payload.permissions,
        isAuthenticated: true,
        isLoading: false,
      });
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Ocorreu um erro inesperado.';
      if (msg.toLowerCase().includes('invalid')) {
        setError('E-mail ou senha inválidos. Por favor, tente novamente.');
      } else {
        setError(msg);
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{ background: '#070a12' }}
    >
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 20% 0%, rgba(0,174,255,0.12) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 80% 100%, rgba(63,255,255,0.08) 0%, transparent 60%)',
        }}
      />

      <div
        className="absolute top-1/4 -left-32 w-96 h-96 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(0,174,255,0.06) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />
      <div
        className="absolute bottom-1/4 -right-32 w-96 h-96 rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(106,255,107,0.05) 0%, transparent 70%)',
          filter: 'blur(40px)',
        }}
      />

      <div className="w-full max-w-sm relative z-10">
        <div className="text-center mb-10">
          <div className="relative inline-flex mb-6">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #00aeff 0%, #3fffff 100%)',
                boxShadow: '0 0 40px rgba(0,174,255,0.5), 0 0 80px rgba(0,174,255,0.2)',
              }}
            >
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div
              className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center"
              style={{ background: '#6aff6b', boxShadow: '0 0 12px rgba(106,255,107,0.6)' }}
            >
              <Zap className="w-2.5 h-2.5 text-black" />
            </div>
          </div>

          <h1 className="text-3xl font-bold text-white tracking-tight mb-1">
            Access<span style={{ color: '#00aeff' }}>Control</span>
          </h1>
          <p className="text-sm mt-1" style={{ color: '#4d5a72' }}>
            Faça login na sua conta
          </p>
        </div>

        <div
          className="rounded-2xl p-8"
          style={{
            background: 'rgba(20,27,45,0.8)',
            border: '1px solid rgba(0,174,255,0.15)',
            backdropFilter: 'blur(20px)',
            boxShadow: '0 0 0 1px rgba(255,255,255,0.04), 0 24px 48px rgba(0,0,0,0.5)',
          }}
        >
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="email" className="block text-sm font-semibold mb-2" style={{ color: '#adb8cc' }}>
                E-mail
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl px-4 py-3 text-white text-sm focus:outline-none transition-all"
                style={{
                  background: 'rgba(15,17,23,0.8)',
                  border: '1px solid rgba(45,58,86,0.8)',
                }}
                onFocus={(e) => { e.currentTarget.style.border = '1px solid rgba(0,174,255,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(0,174,255,0.08)'; }}
                onBlur={(e)  => { e.currentTarget.style.border = '1px solid rgba(45,58,86,0.8)';  e.currentTarget.style.boxShadow = 'none'; }}
                placeholder="voce@empresa.com"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold mb-2" style={{ color: '#adb8cc' }}>
                Senha
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl px-4 py-3 text-white text-sm pr-12 focus:outline-none transition-all"
                  style={{
                    background: 'rgba(15,17,23,0.8)',
                    border: '1px solid rgba(45,58,86,0.8)',
                  }}
                  onFocus={(e) => { e.currentTarget.style.border = '1px solid rgba(0,174,255,0.5)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(0,174,255,0.08)'; }}
                  onBlur={(e)  => { e.currentTarget.style.border = '1px solid rgba(45,58,86,0.8)';  e.currentTarget.style.boxShadow = 'none'; }}
                  placeholder="••••••••"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: '#4d5a72' }}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div
                className="flex items-start gap-3 rounded-xl px-4 py-3"
                style={{ background: 'rgba(255,80,80,0.08)', border: '1px solid rgba(255,80,80,0.2)' }}
              >
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#ff5050' }} />
                <p className="text-sm" style={{ color: '#ff8080' }}>{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full font-semibold py-3 rounded-xl text-sm transition-all flex items-center justify-center gap-2 mt-2 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: isLoading
                  ? 'rgba(0,174,255,0.5)'
                  : 'linear-gradient(135deg, #00aeff 0%, #3fffff 100%)',
                boxShadow: isLoading ? 'none' : '0 0 24px rgba(0,174,255,0.4)',
              }}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  <span>Entrando...</span>
                </>
              ) : (
                'Entrar'
              )}
            </button>
          </form>
        </div>

        <div className="flex items-center justify-center gap-2 mt-6">
          <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#6aff6b', boxShadow: '0 0 6px rgba(106,255,107,0.6)' }} />
          <p className="text-xs" style={{ color: '#4d5a72' }}>
            Sistema de Controle de Acesso Baseado em Perfis
          </p>
        </div>
      </div>
    </div>
  );
}
