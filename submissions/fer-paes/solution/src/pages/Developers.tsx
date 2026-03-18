import { useState } from 'react';
import {
  Code2, Copy, Check, ChevronRight, Globe, MessageSquare, Mail,
  Bot, Terminal, BookOpen, Shield, Zap, AlertCircle, ExternalLink,
} from 'lucide-react';

const BASE_URL = import.meta.env.VITE_SUPABASE_URL;
const ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;
const INGEST_URL = `${BASE_URL}/functions/v1/channel-ingest`;

type Lang = 'curl' | 'javascript' | 'python';

function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <div className="relative group rounded-xl overflow-hidden border border-white/5">
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800/60 border-b border-white/5">
        <span className="text-xs font-mono text-slate-500">{lang ?? 'text'}</span>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-white transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          {copied ? 'Copiado' : 'Copiar'}
        </button>
      </div>
      <pre className="px-4 py-4 bg-slate-900/80 overflow-x-auto text-xs leading-relaxed">
        <code className="text-slate-200 font-mono">{code}</code>
      </pre>
    </div>
  );
}

const SAMPLES: Record<'chat' | 'email' | 'api', Record<Lang, string>> = {
  chat: {
    curl: `curl -X POST ${INGEST_URL}/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk_live_sua_chave_aqui" \\
  -d '{
    "session_id": "session_abc123",
    "name": "Maria Silva",
    "email": "maria@exemplo.com",
    "phone": "+5511999990000",
    "message": "Ola, preciso de ajuda com meu pedido"
  }'`,
    javascript: `const response = await fetch('${INGEST_URL}/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'sk_live_sua_chave_aqui',
  },
  body: JSON.stringify({
    session_id: 'session_abc123',
    name: 'Maria Silva',
    email: 'maria@exemplo.com',
    phone: '+5511999990000',
    message: 'Ola, preciso de ajuda com meu pedido',
  }),
});

const data = await response.json();
console.log('Ticket criado:', data.ticket_id);`,
    python: `import requests

response = requests.post(
    '${INGEST_URL}/chat',
    headers={
        'Content-Type': 'application/json',
        'X-API-Key': 'sk_live_sua_chave_aqui',
    },
    json={
        'session_id': 'session_abc123',
        'name': 'Maria Silva',
        'email': 'maria@exemplo.com',
        'phone': '+5511999990000',
        'message': 'Ola, preciso de ajuda com meu pedido',
    }
)

data = response.json()
print('Ticket criado:', data.get('ticket_id'))`,
  },
  email: {
    curl: `curl -X POST ${INGEST_URL}/email \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk_live_sua_chave_aqui" \\
  -d '{
    "from_email": "cliente@exemplo.com",
    "from_name": "Joao Santos",
    "subject": "Solicitacao de suporte",
    "body": "Bom dia, gostaria de reportar um problema...",
    "attachments": []
  }'`,
    javascript: `const response = await fetch('${INGEST_URL}/email', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'sk_live_sua_chave_aqui',
  },
  body: JSON.stringify({
    from_email: 'cliente@exemplo.com',
    from_name: 'Joao Santos',
    subject: 'Solicitacao de suporte',
    body: 'Bom dia, gostaria de reportar um problema...',
    attachments: [],
  }),
});

const data = await response.json();
console.log('Ticket criado:', data.ticket_id);`,
    python: `import requests

response = requests.post(
    '${INGEST_URL}/email',
    headers={
        'Content-Type': 'application/json',
        'X-API-Key': 'sk_live_sua_chave_aqui',
    },
    json={
        'from_email': 'cliente@exemplo.com',
        'from_name': 'Joao Santos',
        'subject': 'Solicitacao de suporte',
        'body': 'Bom dia, gostaria de reportar um problema...',
        'attachments': [],
    }
)

data = response.json()
print('Ticket criado:', data.get('ticket_id'))`,
  },
  api: {
    curl: `curl -X POST ${INGEST_URL}/api \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: sk_live_sua_chave_aqui" \\
  -d '{
    "external_id": "crm_lead_789",
    "customer": {
      "name": "Ana Oliveira",
      "email": "ana@empresa.com",
      "phone": "+5521888880000",
      "external_id": "crm_cust_456"
    },
    "message": {
      "content": "Lead qualificado - interessado no plano Pro",
      "type": "text"
    },
    "subject": "Lead Qualificado",
    "priority": "high"
  }'`,
    javascript: `const response = await fetch('${INGEST_URL}/api', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'sk_live_sua_chave_aqui',
  },
  body: JSON.stringify({
    external_id: 'crm_lead_789',
    customer: {
      name: 'Ana Oliveira',
      email: 'ana@empresa.com',
      phone: '+5521888880000',
      external_id: 'crm_cust_456',
    },
    message: {
      content: 'Lead qualificado - interessado no plano Pro',
      type: 'text',
    },
    subject: 'Lead Qualificado',
    priority: 'high',
  }),
});

const data = await response.json();
console.log('Ticket:', data.ticket_id, '| Cliente:', data.customer_id);`,
    python: `import requests

response = requests.post(
    '${INGEST_URL}/api',
    headers={
        'Content-Type': 'application/json',
        'X-API-Key': 'sk_live_sua_chave_aqui',
    },
    json={
        'external_id': 'crm_lead_789',
        'customer': {
            'name': 'Ana Oliveira',
            'email': 'ana@empresa.com',
            'phone': '+5521888880000',
            'external_id': 'crm_cust_456',
        },
        'message': {
            'content': 'Lead qualificado - interessado no plano Pro',
            'type': 'text',
        },
        'subject': 'Lead Qualificado',
        'priority': 'high',
    }
)

data = response.json()
print('Ticket:', data.get('ticket_id'), '| Cliente:', data.get('customer_id'))`,
  },
};

const CHAT_WIDGET_CODE = `<!-- Cole este script antes do </body> em qualquer pagina do seu site -->
<script>
  window.ACConfig = {
    apiKey: 'sk_live_sua_chave_aqui',
    primaryColor: '#00aeff',
    title: 'Suporte',
    welcomeMessage: 'Ola! Como posso ajudar?',
  };
</script>
<script src="${BASE_URL}/storage/v1/object/public/widget/chat-widget.js" async></script>`;

interface EndpointCardProps {
  method: string;
  path: string;
  description: string;
  channel: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  fields: Array<{ name: string; type: string; required: boolean; description: string }>;
}

function EndpointCard({ method, path, description, channel, icon: Icon, color, fields }: EndpointCardProps) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-4 px-5 py-4 hover:bg-white/[0.02] transition-colors text-left"
      >
        <div className={`w-8 h-8 rounded-lg ${color} flex items-center justify-center shrink-0`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 font-mono">
              {method}
            </span>
            <code className="text-sm text-white font-mono">{path}</code>
            <span className="text-xs text-slate-500 border border-white/5 rounded-full px-2 py-0.5">
              {channel}
            </span>
          </div>
          <p className="text-slate-400 text-xs mt-0.5">{description}</p>
        </div>
        <ChevronRight className={`w-4 h-4 text-slate-500 shrink-0 transition-transform ${open ? 'rotate-90' : ''}`} />
      </button>

      {open && (
        <div className="border-t border-white/5 px-5 py-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Campos do Payload</p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left py-2 text-slate-500 font-medium pr-4">Campo</th>
                  <th className="text-left py-2 text-slate-500 font-medium pr-4">Tipo</th>
                  <th className="text-left py-2 text-slate-500 font-medium pr-4">Obrig.</th>
                  <th className="text-left py-2 text-slate-500 font-medium">Descricao</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {fields.map((f) => (
                  <tr key={f.name}>
                    <td className="py-2 pr-4">
                      <code className="text-emerald-300 font-mono">{f.name}</code>
                    </td>
                    <td className="py-2 pr-4">
                      <code className="text-blue-300 font-mono">{f.type}</code>
                    </td>
                    <td className="py-2 pr-4">
                      {f.required ? (
                        <span className="text-amber-400">sim</span>
                      ) : (
                        <span className="text-slate-600">nao</span>
                      )}
                    </td>
                    <td className="py-2 text-slate-400">{f.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Developers() {
  const [selectedChannel, setSelectedChannel] = useState<'chat' | 'email' | 'api'>('chat');
  const [lang, setLang] = useState<Lang>('curl');

  const channels: Array<{ id: 'chat' | 'email' | 'api'; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'chat',  label: 'Chat',   icon: MessageSquare },
    { id: 'email', label: 'E-mail', icon: Mail },
    { id: 'api',   label: 'API',    icon: Globe },
  ];

  const langs: Array<{ id: Lang; label: string }> = [
    { id: 'curl',       label: 'cURL' },
    { id: 'javascript', label: 'JavaScript' },
    { id: 'python',     label: 'Python' },
  ];

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-950 overflow-auto">
      <div className="px-8 py-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600/20 flex items-center justify-center">
            <Code2 className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-white font-semibold text-lg">Documentacao para Desenvolvedores</h1>
            <p className="text-slate-400 text-sm mt-0.5">
              Integre qualquer sistema externo — site, bot, CRM, WhatsApp — em minutos
            </p>
          </div>
        </div>
      </div>

      <div className="px-8 py-8 max-w-5xl space-y-10">

        {/* Quick Start */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-4 h-4 text-amber-400" />
            <h2 className="text-white font-semibold">Quick Start</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[
              {
                step: '1',
                title: 'Gere uma API Key',
                desc: 'Va em Integracoes e crie uma chave com os escopos necessarios para sua integracao.',
                color: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
              },
              {
                step: '2',
                title: 'Envie mensagens',
                desc: 'Faca um POST para o endpoint do canal desejado com a chave no header X-API-Key.',
                color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
              },
              {
                step: '3',
                title: 'Acompanhe os tickets',
                desc: 'Cada mensagem cria ou reabre automaticamente um ticket com o cliente identificado.',
                color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
              },
            ].map((item) => (
              <div key={item.step} className={`rounded-xl border p-4 ${item.color}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mb-3 ${item.color}`}>
                  {item.step}
                </div>
                <p className="font-semibold text-sm mb-1">{item.title}</p>
                <p className="text-xs opacity-70">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Authentication */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-slate-400" />
            <h2 className="text-white font-semibold">Autenticacao</h2>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl p-5 space-y-4">
            <p className="text-slate-300 text-sm">
              Todas as chamadas devem incluir o header <code className="text-emerald-300 font-mono bg-emerald-500/10 px-1.5 py-0.5 rounded text-xs">X-API-Key</code> com
              uma chave gerada na pagina de Integracoes.
            </p>
            <CodeBlock lang="http-header" code={`POST /functions/v1/channel-ingest/{type}
Content-Type: application/json
X-API-Key: sk_live_sua_chave_aqui`} />
            <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-lg bg-amber-500/5 border border-amber-500/15">
              <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
              <p className="text-amber-300/70 text-xs">
                Nunca exponha sua API Key em codigo client-side publico. Para chat widgets embutidos
                no site, use um backend intermediario ou a chave publica do widget dedicado.
              </p>
            </div>
          </div>
        </section>

        {/* Endpoints Reference */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Terminal className="w-4 h-4 text-slate-400" />
            <h2 className="text-white font-semibold">Endpoints Disponiveis</h2>
          </div>
          <div className="space-y-3">
            <EndpointCard
              method="POST"
              path="/channel-ingest/chat"
              description="Recebe mensagens de chat ao vivo, widgets de site, aplicativos de mensagem"
              channel="Chat / Widget"
              icon={MessageSquare}
              color="bg-blue-600"
              fields={[
                { name: 'session_id', type: 'string', required: true,  description: 'ID unico da sessao do visitante (agrupa mensagens em um ticket)' },
                { name: 'message',   type: 'string', required: true,  description: 'Conteudo da mensagem do cliente' },
                { name: 'name',      type: 'string', required: false, description: 'Nome do cliente' },
                { name: 'email',     type: 'string', required: false, description: 'E-mail do cliente (usado para identificacao)' },
                { name: 'phone',     type: 'string', required: false, description: 'Telefone do cliente' },
                { name: 'metadata',  type: 'object', required: false, description: 'Dados extras em JSON (pagina de origem, UTMs, etc.)' },
              ]}
            />
            <EndpointCard
              method="POST"
              path="/channel-ingest/email"
              description="Processa e-mails recebidos encaminhados por webhook do seu provedor de e-mail"
              channel="E-mail"
              icon={Mail}
              color="bg-amber-600"
              fields={[
                { name: 'from_email',   type: 'string',   required: true,  description: 'Endereco de e-mail do remetente' },
                { name: 'from_name',    type: 'string',   required: false, description: 'Nome do remetente' },
                { name: 'subject',      type: 'string',   required: true,  description: 'Assunto do e-mail' },
                { name: 'body',         type: 'string',   required: true,  description: 'Corpo do e-mail (texto ou HTML)' },
                { name: 'attachments',  type: 'array',    required: false, description: 'Lista de anexos [{filename, url, content_type}]' },
                { name: 'external_id',  type: 'string',   required: false, description: 'ID da mensagem no provedor de e-mail (anti-duplicacao)' },
              ]}
            />
            <EndpointCard
              method="POST"
              path="/channel-ingest/api"
              description="Integracao generica para CRMs, ERPs, bots, automacoes e sistemas customizados"
              channel="API Generica"
              icon={Bot}
              color="bg-emerald-600"
              fields={[
                { name: 'external_id',       type: 'string', required: false, description: 'ID no sistema de origem (evita duplicatas)' },
                { name: 'customer.name',      type: 'string', required: false, description: 'Nome do cliente' },
                { name: 'customer.email',     type: 'string', required: false, description: 'E-mail do cliente' },
                { name: 'customer.phone',     type: 'string', required: false, description: 'Telefone do cliente' },
                { name: 'customer.external_id', type: 'string', required: false, description: 'ID do cliente no sistema de origem' },
                { name: 'message.content',   type: 'string', required: true,  description: 'Conteudo da mensagem / descricao do caso' },
                { name: 'message.type',      type: 'string', required: false, description: 'Tipo: text | html | structured (default: text)' },
                { name: 'subject',           type: 'string', required: false, description: 'Assunto ou titulo do ticket' },
                { name: 'priority',          type: 'string', required: false, description: 'Prioridade: low | normal | high | urgent' },
                { name: 'attachments',       type: 'array',  required: false, description: 'Lista de anexos [{filename, url, content_type}]' },
              ]}
            />
          </div>
        </section>

        {/* Response Format */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="w-4 h-4 text-slate-400" />
            <h2 className="text-white font-semibold">Formato de Resposta</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">Sucesso (200)</p>
              <CodeBlock lang="json" code={`{
  "ticket_id": "uuid-do-ticket",
  "customer_id": "uuid-do-cliente",
  "conversation_id": "uuid-da-conversa",
  "message_id": "uuid-da-mensagem",
  "is_new_ticket": true
}`} />
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">Erro (4xx / 5xx)</p>
              <CodeBlock lang="json" code={`{
  "error": "Descricao do erro",
  "code": "INVALID_API_KEY"
}`} />
            </div>
          </div>
        </section>

        {/* Code Examples */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Code2 className="w-4 h-4 text-slate-400" />
            <h2 className="text-white font-semibold">Exemplos de Codigo</h2>
          </div>

          <div className="flex gap-2 mb-4 flex-wrap">
            <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-lg p-1">
              {channels.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedChannel(c.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    selectedChannel === c.id
                      ? 'bg-white/10 text-white'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  <c.icon className="w-3.5 h-3.5" />
                  {c.label}
                </button>
              ))}
            </div>

            <div className="flex gap-1 bg-slate-900 border border-white/5 rounded-lg p-1">
              {langs.map((l) => (
                <button
                  key={l.id}
                  onClick={() => setLang(l.id)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                    lang === l.id
                      ? 'bg-white/10 text-white'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <CodeBlock lang={lang} code={SAMPLES[selectedChannel][lang]} />
        </section>

        {/* Chat Widget */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-4 h-4 text-slate-400" />
            <h2 className="text-white font-semibold">Widget de Chat para Websites</h2>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl p-5 space-y-4">
            <p className="text-slate-300 text-sm">
              Adicione o widget de chat ao seu site colando o seguinte trecho de codigo. As mensagens
              dos visitantes serao criadas automaticamente como tickets na plataforma.
            </p>
            <CodeBlock lang="html" code={CHAT_WIDGET_CODE} />
            <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-lg bg-blue-500/5 border border-blue-500/15">
              <AlertCircle className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
              <p className="text-blue-300/70 text-xs">
                O widget usa uma chave publica de escopo restrito. Para configurar o widget,
                crie uma chave com o escopo <code className="font-mono">channel:ingest</code> e
                canal <code className="font-mono">chat</code>.
              </p>
            </div>
          </div>
        </section>

        {/* Rate Limits */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-4 h-4 text-slate-400" />
            <h2 className="text-white font-semibold">Limites de Taxa</h2>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left px-5 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Endpoint</th>
                  <th className="text-center px-5 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Padrao</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Notas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {[
                  { endpoint: '/channel-ingest/chat',  rate: '60 / min',  note: 'Configuravel por chave' },
                  { endpoint: '/channel-ingest/email', rate: '60 / min',  note: 'Configuravel por chave' },
                  { endpoint: '/channel-ingest/api',   rate: '60 / min',  note: 'Configuravel por chave' },
                ].map((row) => (
                  <tr key={row.endpoint} className="hover:bg-white/[0.02]">
                    <td className="px-5 py-3">
                      <code className="text-xs font-mono text-slate-300">{row.endpoint}</code>
                    </td>
                    <td className="px-5 py-3 text-center">
                      <span className="text-emerald-400 text-xs font-medium tabular-nums">{row.rate}</span>
                    </td>
                    <td className="px-5 py-3 text-xs text-slate-500">{row.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-600 mt-2">
            Ao exceder o limite, a API retorna HTTP 429. O header <code className="font-mono">Retry-After</code> indica quantos segundos aguardar.
          </p>
        </section>

        {/* Base URL */}
        <section className="pb-8">
          <div className="flex items-center gap-2 mb-4">
            <ExternalLink className="w-4 h-4 text-slate-400" />
            <h2 className="text-white font-semibold">URL Base</h2>
          </div>
          <div className="bg-slate-900 border border-white/5 rounded-xl p-5">
            <div className="flex items-center gap-3">
              <code className="flex-1 text-sm font-mono text-emerald-300">{INGEST_URL}</code>
              <button
                onClick={() => navigator.clipboard.writeText(INGEST_URL)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <Copy className="w-4 h-4" />
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
