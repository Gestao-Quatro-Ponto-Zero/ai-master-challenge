"use client";

import { useState, useEffect, useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { MiniGame } from "./mini-game";

interface SavedAnalysis {
  result: AnalysisResult;
  analyzed_at: string;
}

interface NormalizedPost {
  url: string;
  description: string;
  type: string;
  likes: number;
  comments: number;
  shares: number;
  views: number;
  engagement_rate: number;
  engagement_by_followers: number;
}

interface AnalysisResult {
  profile: string;
  platform: string;
  source: "dataset" | "new";
  apify_used: boolean;
  apify_error?: string;
  posts?: NormalizedPost[];
  profile_info?: {
    followers: number;
    following: number;
    postsCount: number;
    fullName: string;
    biography: string;
    verified: boolean;
  };
  summary?: {
    avg_engagement: number;
    avg_engagement_by_followers: number;
    avg_views: number;
    avg_likes: number;
    avg_comments: number;
    total_posts: number;
    followers: number;
    best_post?: NormalizedPost;
    worst_post?: NormalizedPost;
  };
  dataset_info?: {
    score: number;
    action: string;
    tier: string;
    primary_platform: string;
    primary_category: string;
    avg_engagement?: number;
  };
  benchmark: {
    avg_engagement: number;
    source_label: string;
    sample_size: number;
  };
  comparison?: {
    delta: number;
    verdict: string;
  };
  note?: string;
  needs_niche?: boolean;
  error?: string;
}

export function ProfileAnalysis() {
  const [username, setUsername] = useState("");
  const [platform, setPlatform] = useState("Instagram");
  const [niche, setNiche] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [needsNiche, setNeedsNiche] = useState(false);
  const [showGame, setShowGame] = useState(false);
  const [history, setHistory] = useState<SavedAnalysis[]>([]);

  // Carregar histórico do localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("g4_profile_analyses");
      if (saved) setHistory(JSON.parse(saved));
    } catch { /* empty */ }
  }, []);

  function saveToHistory(data: AnalysisResult) {
    const entry: SavedAnalysis = { result: data, analyzed_at: new Date().toISOString() };
    const updated = [entry, ...history.filter((h) => h.result.profile !== data.profile || h.result.platform !== data.platform)].slice(0, 20);
    setHistory(updated);
    localStorage.setItem("g4_profile_analyses", JSON.stringify(updated));
  }

  function removeFromHistory(profile: string, platform: string) {
    const updated = history.filter((h) => !(h.result.profile === profile && h.result.platform === platform));
    setHistory(updated);
    localStorage.setItem("g4_profile_analyses", JSON.stringify(updated));
  }

  function loadFromHistory(saved: SavedAnalysis) {
    setResult(saved.result);
    setUsername(saved.result.profile);
    setPlatform(saved.result.platform);
  }

  async function handleAnalyze() {
    if (!username) return;
    setLoading(true);
    setError("");
    setResult(null);
    setNeedsNiche(false);

    try {
      const res = await fetch("/api/profile-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), platform, niche: niche || undefined }),
      });
      const data: AnalysisResult = await res.json();

      if (data.needs_niche) {
        setNeedsNiche(true);
      } else if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
        saveToHistory(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao analisar perfil");
    }
    setLoading(false);
    setShowGame(false);
  }

  return (
    <div className="space-y-4">
      {/* Input */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Análise de Perfil</h3>
        <p className="text-xs text-slate-500 mb-4">
          Busque um perfil ou cole o link. O sistema coleta os últimos posts via Apify e cruza com o dataset.
        </p>

        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="@usuario, usuario ou link do perfil"
            className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#E8734A]/30"
            onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          />
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} className="px-3 py-2 text-sm border border-slate-200 rounded-lg">
            <option>Instagram</option>
            <option>TikTok</option>
            <option>YouTube</option>
            <option>RedNote</option>
            <option>Bilibili</option>
          </select>
          <button onClick={handleAnalyze} disabled={!username || loading} className="px-4 py-2 bg-[#E8734A] text-white text-sm rounded-lg hover:bg-[#d4653f] disabled:opacity-50">
            {loading ? "Analisando..." : "Analisar"}
          </button>
        </div>

        {needsNiche && (
          <div className="flex gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-xs text-amber-700 self-center">Influenciador não encontrado no dataset. Selecione o mercado:</p>
            <select value={niche} onChange={(e) => setNiche(e.target.value)} className="px-3 py-1.5 text-sm border border-amber-200 rounded-lg">
              <option value="">Selecione...</option>
              <option value="beauty">Beleza</option>
              <option value="lifestyle">Estilo de Vida</option>
              <option value="tech">Tecnologia</option>
            </select>
            <button onClick={handleAnalyze} disabled={!niche || loading} className="px-3 py-1.5 bg-amber-600 text-white text-xs rounded-lg hover:bg-amber-700 disabled:opacity-50">
              Comparar
            </button>
          </div>
        )}

        {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">{error}</div>}
      </div>

      {/* Loading com jogo */}
      {loading && (
        <div className="bg-white rounded-2xl border border-[#E8734A]/20 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 border-2 border-[#E8734A] border-t-transparent rounded-full animate-spin" />
            <div>
              <h4 className="text-sm font-semibold text-[#0F1B2D]">Coletando e analisando posts via Apify...</h4>
              <p className="text-xs text-slate-500">Isso pode levar até 1 minuto dependendo da plataforma</p>
            </div>
          </div>

          <div className="p-2.5 bg-amber-50 border border-amber-100 rounded-lg mb-3">
            <p className="text-[10px] text-amber-700">Não saia desta página durante a análise. Os dados estão sendo coletados em tempo real.</p>
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={() => setShowGame(!showGame)}
              className="px-3 py-1 text-[10px] bg-[#0F1B2D] text-white rounded-lg hover:bg-[#1A2D47] transition-colors"
            >
              {showGame ? "Fechar jogo" : "Jogar enquanto espera"}
            </button>
          </div>

          {showGame && (
            <div className="mt-3">
              <MiniGame onClose={() => setShowGame(false)} />
            </div>
          )}
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div className="space-y-4">
          {/* Fonte */}
          <div className={`flex items-center gap-2 p-3 rounded-lg text-xs ${
            result.apify_used ? "bg-emerald-50 border border-emerald-200 text-emerald-700" : "bg-slate-50 border border-slate-200 text-slate-600"
          }`}>
            <span className={`w-2 h-2 rounded-full ${result.apify_used ? "bg-emerald-400" : "bg-slate-400"}`} />
            {result.apify_used
              ? `${result.summary?.total_posts || 0} posts coletados via Apify · @${result.profile} · ${result.platform}`
              : result.apify_error || result.note || "Dados do dataset"
            }
          </div>

          {/* Dataset info */}
          {result.dataset_info && (
            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 bg-slate-100 rounded-lg text-[10px] text-slate-600">Score: {result.dataset_info.score}/100</span>
              <span className="px-2 py-1 bg-slate-100 rounded-lg text-[10px] text-slate-600">Tier: {result.dataset_info.tier}</span>
              <span className="px-2 py-1 bg-slate-100 rounded-lg text-[10px] text-slate-600">Ação: {result.dataset_info.action}</span>
              <span className="px-2 py-1 bg-slate-100 rounded-lg text-[10px] text-slate-600">{result.dataset_info.primary_platform} · {result.dataset_info.primary_category}</span>
            </div>
          )}

          {/* Dados do perfil */}
          {result.profile_info && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-[#0F1B2D]">
                    {result.profile_info.fullName || `@${result.profile}`}
                    {result.profile_info.verified && <span className="ml-1 text-blue-500 text-xs">&#10003;</span>}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5 max-w-md truncate">{result.profile_info.biography}</p>
                </div>
                <div className="flex gap-4 text-center">
                  <div>
                    <p className="text-lg font-bold text-[#0F1B2D]">{result.profile_info.followers.toLocaleString("pt-BR")}</p>
                    <p className="text-[10px] text-slate-400">seguidores</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-[#0F1B2D]">{result.profile_info.postsCount.toLocaleString("pt-BR")}</p>
                    <p className="text-[10px] text-slate-400">posts</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-[#0F1B2D]">{result.profile_info.following.toLocaleString("pt-BR")}</p>
                    <p className="text-[10px] text-slate-400">seguindo</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Cards de métricas */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Engagement por seguidores (padrão da indústria) */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Eng. por Seguidores</p>
              <p className="text-2xl font-bold text-[#0F1B2D] mt-1">
                {(result.summary?.avg_engagement_by_followers ?? 0).toFixed(2)}%
              </p>
              <p className="text-[10px] text-slate-500">(likes+comments) / seguidores</p>
            </div>

            {/* Engagement por views (só vídeos) */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Eng. por Views</p>
              <p className="text-2xl font-bold text-[#0F1B2D] mt-1">
                {(result.summary?.avg_engagement ?? (result.dataset_info?.avg_engagement as number) ?? 0).toFixed(1)}%
              </p>
              <p className="text-[10px] text-slate-500">{result.summary?.total_posts || 0} posts · só vídeos têm views reais</p>
            </div>

            {/* Benchmark */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Benchmark Dataset</p>
              <p className="text-2xl font-bold text-slate-400 mt-1">{result.benchmark.avg_engagement.toFixed(1)}%</p>
              <p className="text-[10px] text-slate-500">{result.benchmark.source_label}</p>
            </div>

            {/* Média de interações */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
              <p className="text-[10px] text-slate-400 uppercase tracking-wider">Média por Post</p>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-lg font-bold text-[#0F1B2D]">{(result.summary?.avg_likes || 0).toLocaleString("pt-BR")}</span>
                <span className="text-[10px] text-slate-400">likes</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold text-[#0F1B2D]">{(result.summary?.avg_comments || 0).toLocaleString("pt-BR")}</span>
                <span className="text-[10px] text-slate-400">comentários</span>
              </div>
            </div>
          </div>

          {/* Análise detalhada dos posts */}
          <PostAnalysisSection posts={result.posts || []} benchmark={result.benchmark.avg_engagement} />
        </div>
      )}
      {/* Disclaimer */}
      {result && (
        <div className="bg-amber-50 rounded-xl border border-amber-100 p-3 text-[10px] text-amber-700">
          Engagement de vídeos usa views reais. Carrosséis e imagens não têm views públicas no Instagram — o engagement é estimado com base em likes.
          Benchmark do dataset tem diferenças pequenas (~0.1-0.2%).
        </div>
      )}

      {/* Histórico de análises */}
      {history.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h4 className="text-sm font-semibold text-[#0F1B2D] mb-3">Análises anteriores</h4>
          <div className="space-y-2">
            {history.map((h, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <button onClick={() => loadFromHistory(h)} className="flex-1 text-left min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-[#0F1B2D]">@{h.result.profile}</span>
                    <span className="text-[10px] text-slate-400">{h.result.platform}</span>
                    {h.result.apify_used && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                    <span>Engagement: {h.result.summary?.avg_engagement?.toFixed(1) || "—"}%</span>
                    <span>· {new Date(h.analyzed_at).toLocaleDateString("pt-BR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                </button>
                <button
                  onClick={() => removeFromHistory(h.result.profile, h.result.platform)}
                  className="text-slate-300 hover:text-red-400 text-sm ml-2 shrink-0"
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// Análise detalhada dos posts com gráficos
// ============================================================

const TYPE_LABELS: Record<string, string> = { Sidecar: "Carrossel", Video: "Vídeo", Image: "Imagem", normal: "Post" };
const TYPE_COLORS: Record<string, string> = { Vídeo: "#E8734A", Carrossel: "#0F1B2D", Imagem: "#10b981", Post: "#6366f1" };

function PostAnalysisSection({ posts, benchmark }: { posts: NormalizedPost[]; benchmark: number }) {
  const [metric, setMetric] = useState<"views" | "followers">("followers");
  const getEng = (p: NormalizedPost) => metric === "followers" ? p.engagement_by_followers : p.engagement_rate;
  const sorted = useMemo(() => [...posts].sort((a, b) => getEng(b) - getEng(a)), [posts, metric]); // eslint-disable-line react-hooks/exhaustive-deps

  // Agrupar por tipo
  const byType = useMemo(() => {
    const groups: Record<string, { posts: number; avg_eng: number; avg_likes: number; avg_comments: number; avg_views: number; total_likes: number; total_comments: number }> = {};
    for (const post of posts) {
      const label = TYPE_LABELS[post.type] || post.type;
      if (!groups[label]) groups[label] = { posts: 0, avg_eng: 0, avg_likes: 0, avg_comments: 0, avg_views: 0, total_likes: 0, total_comments: 0 };
      groups[label].posts++;
      groups[label].avg_eng += getEng(post);
      groups[label].total_likes += post.likes;
      groups[label].total_comments += post.comments;
      groups[label].avg_views += post.views;
    }
    return Object.entries(groups).map(([type, g]) => ({
      type,
      posts: g.posts,
      engagement: Math.round((g.avg_eng / g.posts) * 100) / 100,
      avg_likes: Math.round(g.total_likes / g.posts),
      avg_comments: Math.round(g.total_comments / g.posts),
      avg_views: Math.round(g.avg_views / g.posts),
    })).sort((a, b) => b.engagement - a.engagement);
  }, [posts, metric]); // eslint-disable-line react-hooks/exhaustive-deps

  // Dados do gráfico de barras por post
  const chartData = useMemo(() => sorted.map((p, i) => ({
    name: `Post ${i + 1}`,
    engagement: getEng(p),
    benchmark: metric === "followers" ? 0 : benchmark, // benchmark do dataset é por views, não por followers
    type: TYPE_LABELS[p.type] || p.type,
  })), [sorted, benchmark, metric]); // eslint-disable-line react-hooks/exhaustive-deps

  if (posts.length === 0) return null;

  return (
    <>
      {/* Gráfico: Engagement por post vs benchmark */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-1">
          <h4 className="text-sm font-semibold text-[#0F1B2D]">Engagement por post</h4>
          <div className="flex gap-1">
            <button onClick={() => setMetric("followers")} className={`px-2 py-1 text-[10px] rounded-lg transition-colors ${metric === "followers" ? "bg-[#0F1B2D] text-white" : "bg-slate-100 text-slate-600"}`}>
              Por seguidores
            </button>
            <button onClick={() => setMetric("views")} className={`px-2 py-1 text-[10px] rounded-lg transition-colors ${metric === "views" ? "bg-[#0F1B2D] text-white" : "bg-slate-100 text-slate-600"}`}>
              Por views
            </button>
          </div>
        </div>
        <p className="text-[10px] text-slate-400 mb-4">
          {metric === "followers" ? "(likes + comments) / seguidores — padrão da indústria, compara todos os formatos" : "(likes + comments) / views — só vídeos têm views reais"}
        </p>
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ left: 0, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" fontSize={10} />
              <YAxis fontSize={10} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                formatter={(value: number, name: string) => [`${value.toFixed(2)}%`, name === "engagement" ? "Engagement" : "Benchmark"]}
                contentStyle={{ fontSize: 11, borderRadius: 8 }}
              />
              <Bar dataKey="engagement" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={TYPE_COLORS[entry.type] || "#E8734A"} />
                ))}
              </Bar>
              {/* Linha de benchmark */}
              <Bar dataKey="benchmark" fill="transparent" stroke="#94a3b8" strokeDasharray="4 4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center gap-4 mt-2">
          {byType.map((t) => (
            <div key={t.type} className="flex items-center gap-1.5 text-[10px] text-slate-500">
              <span className="w-2.5 h-2.5 rounded" style={{ backgroundColor: TYPE_COLORS[t.type] || "#E8734A" }} />
              {t.type}
            </div>
          ))}
          <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span className="w-4 border-t border-dashed border-slate-400" />
            Benchmark dataset
          </div>
        </div>
      </div>

      {/* Resumo por tipo de conteúdo */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h4 className="text-sm font-semibold text-[#0F1B2D] mb-3">Performance por tipo de conteúdo</h4>
        <div className="grid md:grid-cols-3 gap-3">
          {byType.map((t) => (
            <div key={t.type} className="p-4 rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-3 h-3 rounded" style={{ backgroundColor: TYPE_COLORS[t.type] || "#E8734A" }} />
                <span className="text-xs font-semibold text-[#0F1B2D]">{t.type}</span>
                <span className="text-[10px] text-slate-400">({t.posts} {t.posts === 1 ? "post" : "posts"})</span>
              </div>
              <p className="text-xl font-bold text-[#0F1B2D]">{t.engagement}%</p>
              <div className="grid grid-cols-3 gap-2 mt-2 text-[10px] text-slate-500">
                <div>
                  <p className="text-slate-400">Likes</p>
                  <p className="font-medium text-[#0F1B2D]">{t.avg_likes.toLocaleString("pt-BR")}</p>
                </div>
                <div>
                  <p className="text-slate-400">Comentários</p>
                  <p className="font-medium text-[#0F1B2D]">{t.avg_comments.toLocaleString("pt-BR")}</p>
                </div>
                <div>
                  <p className="text-slate-400">Views</p>
                  <p className="font-medium text-[#0F1B2D]">{t.avg_views > 0 ? t.avg_views.toLocaleString("pt-BR") : "—"}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lista de posts */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h4 className="text-sm font-semibold text-[#0F1B2D] mb-3">Detalhes dos posts ({posts.length})</h4>
        <div className="space-y-2">
          {sorted.map((post, i) => (
            <div key={i} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
              <span className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                i === 0 ? "bg-emerald-500 text-white" : i === sorted.length - 1 ? "bg-red-400 text-white" : "bg-slate-200 text-slate-600"
              }`}>{i + 1}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-[#0F1B2D] truncate">{post.description || "Sem descrição"}</p>
                <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                  <span className="w-2 h-2 rounded" style={{ backgroundColor: TYPE_COLORS[TYPE_LABELS[post.type] || post.type] || "#E8734A" }} />
                  <span>{TYPE_LABELS[post.type] || post.type}</span>
                  {post.views > 0 && <span>· {post.views.toLocaleString("pt-BR")} views</span>}
                  {post.likes > 0 && <span>· {post.likes.toLocaleString("pt-BR")} likes</span>}
                  {post.comments > 0 && <span>· {post.comments.toLocaleString("pt-BR")} comentários</span>}
                  {post.url && (
                    <a href={post.url} target="_blank" rel="noopener noreferrer" className="text-[#E8734A] hover:underline ml-1">
                      ver post
                    </a>
                  )}
                </div>
              </div>
              <span className={`text-xs font-bold shrink-0 ${
                getEng(post) > 0 ? "text-[#0F1B2D]" : "text-slate-300"
              }`}>{getEng(post) > 0 ? `${getEng(post)}%` : "—"}</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
