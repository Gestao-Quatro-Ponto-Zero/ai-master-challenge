import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// ============================================================
// NORMALIZAÇÃO
// ============================================================

function normalizeInput(raw: string, platform: string) {
  const input = raw.trim();
  let username = "";
  let inputType: "profile" | "post" = "profile";
  let originalUrl: string | undefined;

  const urlMap: Record<string, string> = {
    "instagram.com": "Instagram", "tiktok.com": "TikTok",
    "youtube.com": "YouTube", "youtu.be": "YouTube",
    "xiaohongshu.com": "RedNote", "bilibili.com": "Bilibili",
  };

  if (input.startsWith("http")) {
    originalUrl = input;
    for (const [d, p] of Object.entries(urlMap)) { if (input.includes(d)) { platform = p; break; } }

    try {
      const url = new URL(input);
      const parts = url.pathname.split("/").filter(Boolean);

      if (input.includes("instagram.com")) {
        if (parts[0] === "p" || parts[0] === "reel" || parts[0] === "tv") { inputType = "post"; }
        else { username = parts[0] || ""; }
      } else if (input.includes("tiktok.com")) {
        username = (parts[0] || "").replace("@", "");
        if (parts.length >= 2 && parts[1] === "video") inputType = "post";
      } else if (input.includes("youtube.com")) {
        if (parts[0] === "watch" || parts[0] === "shorts") { inputType = "post"; }
        else { username = (parts[0] === "channel" || parts[0] === "c") ? (parts[1] || "") : (parts[0] || "").replace("@", ""); }
      } else if (input.includes("xiaohongshu.com")) {
        if (parts[0] === "explore") { inputType = "post"; }
        else if (parts[0] === "user" && parts[1] === "profile") { username = parts[2] || ""; }
      } else if (input.includes("bilibili.com")) {
        if (parts[0] === "video") { inputType = "post"; }
        else { username = parts[0] || ""; }
      }
    } catch { /* */ }
  } else {
    username = input.replace(/^@/, "");
  }

  const profileUrls: Record<string, string> = {
    Instagram: `https://www.instagram.com/${username}/`,
    TikTok: `https://www.tiktok.com/@${username}`,
    YouTube: `https://www.youtube.com/@${username}`,
    RedNote: `https://www.xiaohongshu.com/user/profile/${username}`,
    Bilibili: `https://space.bilibili.com/${username}`,
  };

  return {
    username,
    profileUrl: inputType === "profile" ? (profileUrls[platform] || input) : (originalUrl || input),
    platform,
    inputType,
    originalUrl,
  };
}

// ============================================================
// APIFY
// ============================================================

async function runApifyActor(actor: string, input: Record<string, unknown>): Promise<Record<string, unknown>[] | null> {
  const token = process.env.APIFY_TOKEN;
  if (!token) return null;

  try {
    // Actor names: "apify/instagram-scraper" → "apify~instagram-scraper" para a URL da API
    const actorId = actor.replace("/", "~");
    console.log(`[apify] Iniciando actor ${actorId}...`);
    const runRes = await fetch(`https://api.apify.com/v2/acts/${actorId}/runs?token=${token}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });

    if (!runRes.ok) {
      console.error(`[apify] Actor start failed: ${runRes.status} ${await runRes.text()}`);
      return null;
    }

    const runData = await runRes.json();
    const runId = runData.data?.id;
    const datasetId = runData.data?.defaultDatasetId;
    console.log(`[apify] Run ID: ${runId}, Dataset: ${datasetId}`);

    if (!runId) return null;

    // Poll até concluir (max 120s)
    let status = "RUNNING";
    for (let i = 0; i < 60; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      const sr = await fetch(`https://api.apify.com/v2/actor-runs/${runId}?token=${token}`);
      const sd = await sr.json();
      status = sd.data?.status || "FAILED";
      console.log(`[apify] Poll ${i + 1}: ${status}`);
      if (status !== "RUNNING" && status !== "READY") break;
    }

    if (status !== "SUCCEEDED") {
      console.error(`[apify] Run ${runId} ended with status: ${status}`);
      return null;
    }

    const itemsRes = await fetch(`https://api.apify.com/v2/datasets/${datasetId}/items?token=${token}&limit=10`);
    const items = await itemsRes.json();
    console.log(`[apify] Items coletados: ${Array.isArray(items) ? items.length : 0}`);

    return Array.isArray(items) ? items : null;
  } catch (err) {
    console.error("[apify] Error:", err);
    return null;
  }
}

interface NormalizedPost {
  url: string;
  description: string;
  type: string;
  likes: number;
  comments: number;
  shares: number;
  views: number;
  engagement_rate: number;         // por views (vídeos) ou estimado (imagens)
  engagement_by_followers: number; // por seguidores — padrão da indústria
}

/** Retorna 0 se negativo ou NaN */
function safeNum(v: unknown): number {
  const n = Number(v);
  return (isNaN(n) || n < 0) ? 0 : n;
}

function normalizePost(item: Record<string, unknown>, platform: string, followers = 0): NormalizedPost {
  let likes = 0, comments = 0, shares = 0, views = 0, description = "", url = "", type = "";

  switch (platform) {
    case "Instagram": {
      likes = safeNum(item.likesCount);
      comments = safeNum(item.commentsCount);
      const videoViews = safeNum(item.videoViewCount) || safeNum(item.videoPlayCount);
      // Para Sidecar/Image sem views: estimar views com base em likes
      // Média do Instagram: ~5% engagement → views ≈ likes * 20
      views = videoViews > 0 ? videoViews : (likes > 0 ? likes * 20 : 0);
      description = String(item.caption || "").slice(0, 200);
      url = String(item.url || "");
      type = String(item.type || "Image");
      break;
    }
    case "TikTok":
      likes = safeNum(item.diggCount) || safeNum(item.likes);
      comments = safeNum(item.commentCount) || safeNum(item.comments);
      shares = safeNum(item.shareCount) || safeNum(item.shares);
      views = safeNum(item.playCount) || safeNum(item.plays);
      description = String(item.text || item.desc || "").slice(0, 200);
      url = String(item.webVideoUrl || "");
      type = "Video";
      break;
    case "YouTube":
      likes = safeNum(item.likeCount);
      comments = safeNum(item.commentCount);
      views = safeNum(item.viewCount);
      description = String(item.title || "").slice(0, 200);
      url = String(item.url || "");
      type = "Video";
      break;
    case "RedNote": {
      const pd = (item.postData || item.item || item) as Record<string, unknown>;
      const nc = (pd.note_card || pd) as Record<string, unknown>;
      const interact = (nc.interact_info || nc.interactInfo || {}) as Record<string, unknown>;
      const lc = interact.liked_count || interact.likedCount || 0;
      likes = typeof lc === "string" ? parseInt(lc.replace(/\D/g, "")) || 0 : Number(lc);
      views = Math.max(likes * 10, 1);
      description = String(nc.display_title || pd.displayTitle || "").slice(0, 200);
      url = String(item.link || pd.postUrl || "");
      type = String(nc.type || "normal");
      break;
    }
    case "Bilibili": {
      const parseC = (v: unknown) => {
        if (typeof v === "number") return v;
        if (typeof v !== "string") return 0;
        if (v.includes("万")) return Math.round(parseFloat(v) * 10000);
        return parseInt(v.replace(/\D/g, "")) || 0;
      };
      likes = parseC(item.like_count);
      comments = parseC(item.reply_count);
      shares = parseC(item.share_count);
      views = parseC(item.view_count) || 1;
      description = String(item.title || "").slice(0, 200);
      url = String(item.url || "");
      type = "Video";
      break;
    }
  }

  const eng = views > 0 ? ((likes + shares + comments) / views) * 100 : 0;
  const engByFollowers = followers > 0 ? ((likes + shares + comments) / followers) * 100 : 0;
  return {
    url, description, type, likes, comments, shares, views,
    engagement_rate: Math.round(eng * 100) / 100,
    engagement_by_followers: Math.round(engByFollowers * 100) / 100,
  };
}

function getActorInput(normalized: ReturnType<typeof normalizeInput>) {
  const isProfile = normalized.inputType === "profile";

  switch (normalized.platform) {
    case "Instagram":
      return {
        actor: "apify/instagram-scraper",
        input: {
          addParentData: false,
          directUrls: isProfile
            ? [`https://www.instagram.com/${normalized.username}/`]
            : [normalized.originalUrl || normalized.profileUrl],
          resultsLimit: isProfile ? 5 : 1,
          resultsType: "posts",
          searchLimit: 1,
          searchType: isProfile ? "user" : "hashtag",
        },
      };
    case "TikTok":
      return {
        actor: "clockworks/tiktok-scraper",
        input: {
          commentsPerPost: 0, excludePinnedPosts: false, hashtags: [],
          maxFollowersPerProfile: 0, maxFollowingPerProfile: 0, maxRepliesPerComment: 0,
          proxyCountryCode: "None", resultsPerPage: isProfile ? 5 : 1,
          scrapeRelatedVideos: false, shouldDownloadAvatars: false, shouldDownloadCovers: false,
          shouldDownloadMusicCovers: false, shouldDownloadSlideshowImages: false, shouldDownloadVideos: false,
          ...(isProfile
            ? { profiles: [`https://www.tiktok.com/@${normalized.username}`] }
            : { postURLs: [normalized.originalUrl || normalized.profileUrl] }),
        },
      };
    case "YouTube":
      return {
        actor: "streamers/youtube-scraper",
        input: {
          downloadSubtitles: false, maxResults: isProfile ? 5 : 1,
          maxResultStreams: 0, maxResultsShorts: 0,
          searchQueries: [normalized.username],
        },
      };
    case "RedNote":
      return {
        actor: "easyapi/all-in-one-rednote-xiaohongshu-scraper",
        input: isProfile
          ? { mode: "userPosts", postUrls: [""], profileUrls: [normalized.profileUrl], maxItems: 5 }
          : { mode: "comment", postUrls: [normalized.originalUrl || normalized.profileUrl], profileUrls: [""], maxItems: 1 },
      };
    case "Bilibili":
      return {
        actor: "kuaima/bilibili-detail",
        input: { startUrls: [{ url: normalized.originalUrl || normalized.profileUrl }] },
      };
    default:
      return null;
  }
}

// ============================================================
// DATASET
// ============================================================

function loadBenchmarks() {
  const dir = path.join(process.cwd(), "public", "data");
  let ranking: Record<string, unknown>[] = [];
  let stats: Record<string, unknown> = {};
  let platCat: Record<string, unknown>[] = [];

  try { ranking = (JSON.parse(fs.readFileSync(path.join(dir, "influencer_ranking.json"), "utf-8"))).data || []; } catch { /* */ }
  try { stats = JSON.parse(fs.readFileSync(path.join(dir, "general_stats.json"), "utf-8")); } catch { /* */ }
  try { const p = JSON.parse(fs.readFileSync(path.join(dir, "h3_platform_category.json"), "utf-8")); platCat = p.data || p; } catch { /* */ }

  return { ranking, stats, platCat };
}

// ============================================================
// ROUTE — síncrono, aguarda Apify e retorna resultado completo
// ============================================================

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { username: rawInput, platform: rawPlatform, niche } = body;

    if (!rawInput || !rawPlatform) {
      return NextResponse.json({ error: "Informe o perfil e a plataforma" }, { status: 400 });
    }

    const normalized = normalizeInput(rawInput, rawPlatform);
    const hasApify = !!process.env.APIFY_TOKEN;
    const { ranking, stats, platCat } = loadBenchmarks();

    console.log(`[profile] Input: "${rawInput}" → username="${normalized.username}", platform="${normalized.platform}", type="${normalized.inputType}"`);

    // Dataset match
    const match = normalized.username ? ranking.find(
      (r: Record<string, unknown>) =>
        String(r.creator_name).toLowerCase() === normalized.username.toLowerCase() ||
        String(r.creator_id).toLowerCase() === normalized.username.toLowerCase()
    ) : null;

    // Benchmark
    const overallEng = (stats as Record<string, unknown>).engagement_rate as Record<string, unknown> | undefined;
    const generalBenchmark = Number(overallEng?.mean) || 19.9;

    const nicheBenchmarkEntry = platCat.find(
      (r: Record<string, unknown>) =>
        String(r.platform).toLowerCase() === normalized.platform.toLowerCase() &&
        String(r.content_category).toLowerCase() === (niche || "lifestyle").toLowerCase()
    );
    const nicheBenchmark = Number(nicheBenchmarkEntry?.avg_engagement_rate) || generalBenchmark;
    const benchmarkEng = match ? generalBenchmark : nicheBenchmark;
    const benchmarkLabel = match ? "Dataset geral (52K posts)" : `${niche || "lifestyle"} / ${normalized.platform} (dataset)`;
    const benchmarkSize = match ? (Number((stats as Record<string, unknown>).total_posts) || 52214) : (Number(nicheBenchmarkEntry?.posts) || 10000);

    // Sem Apify e sem match — pedir nicho
    if (!hasApify && !match && !niche) {
      return NextResponse.json({
        needs_niche: true,
        note: "Configure APIFY_TOKEN no .env para coleta de dados reais.",
      });
    }

    // Coletar via Apify (síncrono — aguarda resultado)
    let posts: NormalizedPost[] = [];
    let apifyUsed = false;
    let apifyError = "";
    let profileData: { followers: number; following: number; postsCount: number; fullName: string; biography: string; verified: boolean } | null = null;

    if (hasApify) {
      // STEP 1: Buscar dados do perfil (followers) — só para Instagram por enquanto
      if (normalized.inputType === "profile" && normalized.platform === "Instagram") {
        console.log(`[profile] Buscando dados do perfil @${normalized.username}...`);
        const profileItems = await runApifyActor("apify/instagram-scraper", {
          addParentData: false,
          directUrls: [`https://www.instagram.com/${normalized.username}/`],
          resultsLimit: 1,
          resultsType: "details",
          searchLimit: 1,
          searchType: "user",
        });
        if (profileItems && profileItems.length > 0 && !profileItems[0].error) {
          const p = profileItems[0];
          profileData = {
            followers: safeNum(p.followersCount),
            following: safeNum(p.followsCount),
            postsCount: safeNum(p.postsCount),
            fullName: String(p.fullName || ""),
            biography: String(p.biography || ""),
            verified: Boolean(p.verified),
          };
          console.log(`[profile] Perfil: ${profileData.fullName} | ${profileData.followers.toLocaleString()} seguidores`);
        }
      }

      // STEP 2: Buscar posts
      const actorConfig = getActorInput(normalized);
      if (actorConfig) {
        console.log(`[profile] Buscando posts: ${actorConfig.actor}`);
        const items = await runApifyActor(actorConfig.actor, actorConfig.input);

        if (items && items.length > 0) {
          const validItems = items.filter((item) => !item.error);
          if (validItems.length > 0) {
            const followers = profileData?.followers || 0;
            posts = validItems.map((item) => normalizePost(item, normalized.platform, followers)).filter((p) => p.likes > 0 || p.comments > 0 || p.views > 0);
            apifyUsed = true;
            console.log(`[profile] ${posts.length} posts normalizados (followers: ${followers})`);
          } else {
            apifyError = "Perfil não encontrado ou privado.";
            console.log(`[profile] Todos os itens retornaram erro:`, items.map((i) => i.error));
          }
        } else {
          apifyError = "Apify não retornou dados para este perfil.";
        }
      }
    }

    // Calcular summary dos posts
    let summary = null;
    if (posts.length > 0) {
      const sorted = [...posts].sort((a, b) => b.engagement_rate - a.engagement_rate);
      const avgEng = posts.reduce((a, p) => a + p.engagement_rate, 0) / posts.length;
      const avgEngByFollowers = posts.reduce((a, p) => a + p.engagement_by_followers, 0) / posts.length;
      summary = {
        avg_engagement: Math.round(avgEng * 100) / 100,
        avg_engagement_by_followers: Math.round(avgEngByFollowers * 100) / 100,
        avg_views: Math.round(posts.reduce((a, p) => a + p.views, 0) / posts.length),
        avg_likes: Math.round(posts.reduce((a, p) => a + p.likes, 0) / posts.length),
        avg_comments: Math.round(posts.reduce((a, p) => a + p.comments, 0) / posts.length),
        total_posts: posts.length,
        followers: profileData?.followers || 0,
        best_post: sorted[0],
        worst_post: sorted[sorted.length - 1],
      };
    }

    // Montar delta
    const realEng = summary?.avg_engagement ?? (match ? Number(match.avg_engagement) || 0 : 0);
    const delta = realEng > 0 ? Math.round((realEng - benchmarkEng) * 100) / 100 : null;

    return NextResponse.json({
      profile: normalized.username || rawInput,
      platform: normalized.platform,
      input_type: normalized.inputType,
      source: match ? "dataset" : "new",
      apify_used: apifyUsed,
      apify_error: apifyError || undefined,

      // Dados do perfil
      profile_info: profileData || undefined,

      // Dados reais (Apify)
      posts: apifyUsed ? posts : undefined,
      summary: summary || undefined,

      // Dataset info
      dataset_info: match ? {
        score: match.score,
        action: match.action,
        tier: match.creator_tier,
        primary_platform: match.primary_platform,
        primary_category: match.primary_category,
        avg_engagement: match.avg_engagement,
      } : undefined,

      // Benchmark
      benchmark: {
        avg_engagement: benchmarkEng,
        source_label: benchmarkLabel,
        sample_size: benchmarkSize,
      },

      // Comparação
      comparison: delta !== null ? {
        delta,
        verdict: delta >= 0 ? "Acima do benchmark — tendência positiva" : "Abaixo do benchmark — avaliar custo-benefício",
      } : undefined,

      note: !hasApify
        ? "Configure APIFY_TOKEN no .env para coleta de dados reais"
        : apifyError || (apifyUsed ? `${posts.length} posts coletados via Apify` : undefined),
    });
  } catch (err) {
    console.error("[profile] Error:", err);
    return NextResponse.json({ error: err instanceof Error ? err.message : "Falha na análise" }, { status: 500 });
  }
}
