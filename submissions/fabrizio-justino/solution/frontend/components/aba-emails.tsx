"use client"

import { useEffect, useState } from "react"
import { Loader2, Mail, ShieldCheck } from "lucide-react"
import { Card } from "@/components/ui/card"
import { ia, urlPreviewEmail, type DestinatarioEmail, type EmailsResponse } from "@/lib/api"

const ROTULO_PUBLICO = { equipe: "Equipe (vendedores)", gestao: "Gestão (managers e RevOps)" }

// Pré-visualização dos e-mails automáticos. Enviar NÃO é feito pela tela — só pelo
// job/linha de comando (python -m app.emails --modo enviar).
export function AbaEmails({ data }: { data: string }) {
  const [info, setInfo] = useState<EmailsResponse | null>(null)
  const [erro, setErro] = useState("")
  const [selecionado, setSelecionado] = useState<DestinatarioEmail | null>(null)
  const [carregandoPreview, setCarregandoPreview] = useState(false)

  useEffect(() => {
    ia.emails(data)
      .then((r) => { setInfo(r); setSelecionado(r.emails.find((e) => e.papel === "revops") ?? r.emails[0] ?? null) })
      .catch((e) => setErro(e.message))
  }, [data])

  useEffect(() => { if (selecionado) setCarregandoPreview(true) }, [selecionado])

  if (erro) return <p className="text-sm text-destructive">{erro}</p>
  if (!info) return <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Carregando...</p>

  return (
    <div className="space-y-4">
      <Card className="flex flex-col gap-1 border-border/60 bg-card/70 p-3 text-xs text-muted-foreground md:flex-row md:items-center md:gap-4">
        <span className="flex items-center gap-1 font-semibold text-foreground"><ShieldCheck className="h-4 w-4 text-emerald-500" /> Modo: {info.modo}</span>
        <span>{info.destinatarios_reais ? "Destinatários reais configurados" : "Usando destinatários de exemplo (@example.com)"}</span>
        {info.redirecionar && <span>Envio redirecionado para o endereço de teste</span>}
        <span>IA: {info.ia.ativa ? info.ia.modelo : "desligada (textos automáticos)"}</span>
        <span className="md:ml-auto">Envio: <code>python -m app.emails --data {data} --modo enviar</code></span>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
        <div className="space-y-4">
          {(["gestao", "equipe"] as const).map((p) => (
            <div key={p}>
              <h3 className="mb-1 text-[11px] font-bold uppercase tracking-widest text-primary/80">{ROTULO_PUBLICO[p]}</h3>
              <ul className="max-h-80 space-y-0.5 overflow-y-auto">
                {info.emails.filter((e) => e.publico === p).map((e) => (
                  <li key={e.papel + e.nome}>
                    <button type="button" onClick={() => setSelecionado(e)}
                      className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-primary/5 ${
                        selecionado?.nome === e.nome && selecionado?.papel === e.papel ? "bg-primary/10 font-medium text-primary" : ""
                      }`}>
                      <Mail className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">{e.nome}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="relative min-h-[600px] overflow-hidden rounded-xl border border-border/60 bg-white">
          {selecionado && (
            <>
              <p className="border-b bg-muted/40 px-3 py-1.5 text-xs text-muted-foreground">Para: {selecionado.para.join(", ")}</p>
              {carregandoPreview && (
                <div className="absolute inset-0 top-8 flex items-center justify-center gap-2 bg-white/80 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Montando o e-mail (a IA escreve as seções)...
                </div>
              )}
              <iframe key={selecionado.papel + selecionado.nome + data} title={`E-mail para ${selecionado.nome}`}
                src={urlPreviewEmail(data, selecionado)} onLoad={() => setCarregandoPreview(false)}
                className="h-[760px] w-full" sandbox="" />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
