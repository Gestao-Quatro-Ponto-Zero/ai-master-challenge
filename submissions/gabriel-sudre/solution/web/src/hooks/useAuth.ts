import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { API_BASE } from '../lib/api'
import type { User, Session } from '@supabase/supabase-js'

interface UserProfile {
  id: string
  email: string
  role: 'admin' | 'vendedor' | 'manager'
  sales_team_id: number | null | undefined
  manager_name: string | null | undefined
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setUser(data.session?.user ?? null)
      if (data.session?.user) {
        loadProfile(data.session.user.id, data.session.access_token)
      } else {
        setLoading(false)
      }
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
        if (session?.user) {
          loadProfile(session.user.id, session.access_token)
        } else {
          setProfile(null)
          setLoading(false)
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  async function loadProfile(_userId: string, token: string) {
    try {
      // Load profile via API (uses service key, bypasses RLS)
      const res = await fetch(`${API_BASE}/api/init`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (res.ok) {
        const data = await res.json()
        setProfile(data.profile)
      } else if (res.status === 403) {
        // User exists in auth but not in users table
        setProfile(null)
      } else {
        setProfile(null)
      }
    } catch {
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }

  async function signInWithOtp(email: string) {
    const { error } = await supabase.auth.signInWithOtp({ email })
    if (error) throw error
  }

  async function verifyOtp(email: string, token: string) {
    const { error } = await supabase.auth.verifyOtp({
      email,
      token,
      type: 'email',
    })
    if (error) throw error
  }

  async function signOut() {
    await supabase.auth.signOut()
    setUser(null)
    setProfile(null)
    setSession(null)
  }

  return { user, profile, session, loading, signInWithOtp, verifyOtp, signOut }
}
