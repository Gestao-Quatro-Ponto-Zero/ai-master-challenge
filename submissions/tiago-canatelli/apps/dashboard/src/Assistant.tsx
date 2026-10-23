import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { API_URL, post, type User } from './api'
import { useView } from './hooks'
import { Badge, Card } from './ui'

type Prompt = { slug: string; title: string; profile_slug: string; description: string; body: string; variables: { name: string; default: string }[]; is_customized: boolean; version: number }
type Profile = { slug: string; name: string; question: string; instructions: string; is_customized: boolean }
type Answer = { answer: string; tool_calls: { tool: string; input: unknown }[]; model: string; usage: { input: number; output: number }; latency_ms: number }

function render(body: string, vars: Record<string, string>) {
  return body.replace(/\{\{(\w+)\}\}/g, (_, k: string) => vars[k] ?? `{{${k}}}`)
}

export default function AssistantPage({ initialQuestion, user }: { initialQuestion: string | null; user: User }) {
  const chooseProfile = user.role === 'admin' || user.role === 'executivo'
  const [refresh, setRefresh] = useState(0)
  const prompts = useView<Prompt>('prompts', {}, refresh)
  const profiles = useView<Profile>('profiles', {}, refresh)
  const [slug, setSlug] = useState<string | null>(null)
  const [profile, setProfile] = useState(user.profile_slug ?? 'executivo')
  const [vars, setVars] = useState<Record<string, string>>({})
  const [text, setText] = useState(initialQuestion ?? '')
  const [result, setResult] = useState<Answer | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingProfile, setEditingProfile] = useState(false)
  const prompt = prompts.data?.find((p) => p.slug === slug)
  const prof = profiles.data?.find((p) => p.slug === profile)

  useEffect(() => { if (initialQuestion) { setText(initialQuestion); setSlug(null); if (chooseProfile) setProfile('cs') } }, [initialQuestion, chooseProfile])

  const choose = (p: Prompt) => {
    const v = Object.fromEntries((p.variables ?? []).map((x) => [x.name, x.default]))
    setSlug(p.slug); if (chooseProfile) setProfile(p.profile_slug); setVars(v); setText(render(p.body, v)); setResult(null)
  }

  const ask = async () => {
    setBusy(true); setError(null); setResult(null)
    try { setResult(await post<Answer>('/assistant', { question: text, profile_slug: profile, prompt_slug: slug })) }
    catch (e) { setError((e as Error).message) }
    finally { setBusy(false) }
  }
  const savePrompt = async () => {
    if (!prompt) return
    try { await post(`/prompts/${prompt.slug}`, { text }, 'PUT'); setRefresh((x) => x + 1) } catch (e) { setError((e as Error).message) }
  }
  const restorePrompt = async () => {
    if (!prompt) return
    try { await post(`/prompts/${prompt.slug}/restore`, {}); setRefresh((x) => x + 1); setSlug(null) } catch (e) { setError((e as Error).message) }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
      <div className="space-y-4">
        <Card title="Perguntas prontas" subtitle="Escolha, ajuste o texto e envie" source="api.prompts">
          <ul className="space-y-1 text-sm">
            {(prompts.data ?? []).map((p) => (
              <li key={p.slug}>
                <button onClick={() => choose(p)} className={`w-full rounded-lg px-2 py-1.5 text-left ${slug === p.slug ? 'bg-slate-100 dark:bg-slate-800' : 'hover:bg-slate-50 dark:hover:bg-slate-800'}`}>
                  {p.title} {p.is_customized && <Badge tone="amber">editado</Badge>}
                  <div className="muted text-xs">{profiles.data?.find((x) => x.slug === p.profile_slug)?.name}</div>
                </button>
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Conectar via MCP" subtitle="Mesmas tools no Claude, ChatGPT, Cursor…">
          <pre className="overflow-auto rounded bg-slate-100 p-2 text-[11px] dark:bg-slate-800">{`claude mcp add --transport http ravenstack-churn \\\n  ${API_URL}/mcp \\\n  --header "Authorization: Bearer <MCP_TOKEN>"`}</pre>
        </Card>
      </div>

      <div className="space-y-4">
        <Card title="Pergunte ao analista" subtitle="A IA consulta o lake (views api.*) e responde com Resposta · Por quê · Confiança · Próxima ação">
          <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
            <label className="muted">Analisar como</label>
            <select disabled={!chooseProfile} className="rounded-lg border border-slate-300 bg-transparent px-2 py-1 disabled:opacity-70 dark:border-slate-700" value={profile} onChange={(e) => setProfile(e.target.value)}>
              {(profiles.data ?? []).map((p) => <option key={p.slug} value={p.slug}>{p.name}</option>)}
            </select>
            {prof && <button className="muted text-xs underline" onClick={() => setEditingProfile((x) => !x)}>{editingProfile ? 'fechar perfil' : 'ver/editar perfil'}</button>}
            {prof?.is_customized && <Badge tone="amber">perfil personalizado</Badge>}
          </div>
          {editingProfile && prof && <ProfileEditor canEdit={user.can_edit} profile={prof} onSaved={() => setRefresh((x) => x + 1)} onError={setError} />}
          {prompt && (prompt.variables ?? []).length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {prompt.variables.map((v) => (
                <label key={v.name} className="text-xs">{v.name}{' '}
                  <input className="rounded border border-slate-300 bg-transparent px-1 py-0.5 dark:border-slate-700" value={vars[v.name] ?? ''}
                    onChange={(e) => { const nv = { ...vars, [v.name]: e.target.value }; setVars(nv); setText(render(prompt.body, nv)) }} />
                </label>
              ))}
            </div>
          )}
          <textarea className="h-28 w-full rounded-lg border border-slate-300 bg-transparent p-2 text-sm dark:border-slate-700" value={text} onChange={(e) => setText(e.target.value)} placeholder="Escreva sua pergunta ou escolha uma pronta…" />
          <div className="mt-2 flex flex-wrap gap-2">
            <button disabled={busy || !text.trim()} onClick={ask} className="rounded-lg bg-slate-900 px-4 py-1.5 text-sm text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900">{busy ? 'Analisando…' : 'Perguntar'}</button>
            {prompt && user.can_edit && <button onClick={savePrompt} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-700">Salvar como padrão deste prompt</button>}
            {prompt?.is_customized && user.can_edit && <button onClick={restorePrompt} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-700">Restaurar original</button>}
          </div>
          {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        </Card>

        {busy && <div className="card h-40 animate-pulse" />}
        {result && (
          <Card title="Resposta" subtitle={`${result.model} · ${(result.latency_ms / 1000).toFixed(0)} s · ${result.usage.input + result.usage.output} tokens`}>
            <div className="prose-answer text-sm leading-relaxed"><ReactMarkdown remarkPlugins={[remarkGfm]}>{result.answer}</ReactMarkdown></div>
            {result.tool_calls.length > 0 && (
              <details className="mt-3 text-xs">
                <summary className="muted cursor-pointer">Consultas feitas pela IA ({result.tool_calls.length})</summary>
                <ul className="mt-1 space-y-1">{result.tool_calls.map((c, i) => <li key={i}><code>{c.tool}</code> <code className="muted">{JSON.stringify(c.input)}</code></li>)}</ul>
              </details>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}

function ProfileEditor({ profile, onSaved, onError, canEdit }: { profile: Profile; onSaved: () => void; onError: (e: string) => void; canEdit: boolean }) {
  const [text, setText] = useState(profile.instructions)
  useEffect(() => setText(profile.instructions), [profile])
  const save = async () => { try { await post(`/profiles/${profile.slug}`, { text }, 'PUT'); onSaved() } catch (e) { onError((e as Error).message) } }
  const restore = async () => { try { await post(`/profiles/${profile.slug}/restore`, {}); onSaved() } catch (e) { onError((e as Error).message) } }
  return (
    <div className="mb-3 rounded-lg bg-slate-50 p-2 dark:bg-slate-800">
      <p className="text-xs"><b>{profile.name}:</b> {profile.question}</p>
      <textarea className="mt-1 h-20 w-full rounded border border-slate-300 bg-transparent p-1 text-xs dark:border-slate-700" value={text} onChange={(e) => setText(e.target.value)} />
      {canEdit && <div className="mt-1 flex gap-2 text-xs">
        <button onClick={save} className="rounded border border-slate-300 px-2 py-0.5 dark:border-slate-600">Salvar perfil</button>
        {profile.is_customized && <button onClick={restore} className="rounded border border-slate-300 px-2 py-0.5 dark:border-slate-600">Restaurar padrão</button>}
      </div>}
    </div>
  )
}
