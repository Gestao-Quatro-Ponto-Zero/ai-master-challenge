import { useAuth } from './hooks/useAuth'
import { LoginPage } from './components/LoginPage'
import { Dashboard } from './components/Dashboard'

function App() {
  const { user, profile, loading, signInWithOtp, verifyOtp, signOut } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <p className="text-[var(--text-secondary)]">Carregando...</p>
      </div>
    )
  }

  if (!user || !profile) {
    return <LoginPage onSendOtp={signInWithOtp} onVerifyOtp={verifyOtp} />
  }

  return <Dashboard profile={profile} onSignOut={signOut} />
}

export default App
