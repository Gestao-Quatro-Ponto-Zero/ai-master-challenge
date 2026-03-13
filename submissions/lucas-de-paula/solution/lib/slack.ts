/**
 * slack.ts — Slack Block Kit message builder + Incoming Webhook sender
 *
 * buildMorningBlocks  → top 10 Engaging deals by score
 * buildEveningBlocks  → pipeline summary + top 5 zombies
 * sendSlackBlocks     → POST to Incoming Webhook URL
 */

import { type ScoredDeal } from "@/lib/scoring";
import { getActionTag } from "@/lib/actions";

// ── Helpers ───────────────────────────────────────────────────────────────────

function scoreEmoji(score: number): string {
  if (score >= 70) return "🟢";
  if (score >= 40) return "🟡";
  return "🔴";
}

function daysLabel(days: number): string {
  if (days > 90) return `💀 ${days}d parado`;
  if (days > 30) return `⚠️ ${days}d`;
  return `✅ ${days}d`;
}

function todayBR(): string {
  return new Date().toLocaleDateString("pt-BR", {
    weekday: "long", day: "2-digit", month: "long",
  });
}

// ── Morning ───────────────────────────────────────────────────────────────────

export function buildMorningBlocks(deals: ScoredDeal[]): object[] {
  const active      = deals.filter((d) => d.deal_stage === "Engaging" || d.deal_stage === "Prospecting");
  const top10       = [...active].sort((a, b) => b.score - a.score).slice(0, 10);
  const highPrio    = active.filter((d) => d.score >= 70).length;
  const atRisk      = active.filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 30 && d.days_in_stage <= 90).length;
  const zombies     = active.filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 90).length;
  const prospecting = active.filter((d) => d.deal_stage === "Prospecting").length;

  const blocks: object[] = [
    {
      type: "header",
      text: { type: "plain_text", text: "☀️ Lead Scorer — Prioridades do Dia", emoji: true },
    },
    {
      type: "context",
      elements: [{ type: "mrkdwn", text: `📅 ${todayBR()}` }],
    },
    {
      type: "section",
      fields: [
        { type: "mrkdwn", text: `*Deals ativos*\n${active.length}` },
        { type: "mrkdwn", text: `*🚀 Alta prioridade*\n${highPrio}` },
        { type: "mrkdwn", text: `*⚠️ Em risco (31–90d)*\n${atRisk}` },
        { type: "mrkdwn", text: `*➡️ Prospecting*\n${prospecting}` },
        { type: "mrkdwn", text: `*💀 Zumbis (+90d)*\n${zombies}` },
      ],
    },
    { type: "divider" },
    {
      type: "section",
      text: { type: "mrkdwn", text: "*🎯 Top 10 Deals para focar hoje — por score:*" },
    },
  ];

  top10.forEach((deal, i) => {
    const tag     = getActionTag(deal);
    const urgency = deal.deal_stage === "Engaging" && deal.score >= 70 && deal.days_in_stage <= 30
      ? `_⏱ ${52 - deal.days_in_stage}d para fechar saudável_`
      : deal.days_in_stage > 30 && deal.days_in_stage <= 90
        ? `_${deal.days_in_stage - 30}d além do ideal_`
        : "";

    blocks.push({
      type: "section",
      text: {
        type: "mrkdwn",
        text: [
          `*${i + 1}. ${deal.account || "Sem conta"}* — ${deal.product}`,
          `${scoreEmoji(deal.score)} Score: *${deal.score}* | ${daysLabel(deal.days_in_stage)} | ${tag.label}`,
          `👤 ${deal.sales_agent}${urgency ? ` | ${urgency}` : ""}`,
        ].join("\n"),
      },
    });
  });

  blocks.push({ type: "divider" });
  blocks.push({
    type: "context",
    elements: [
      { type: "mrkdwn", text: "Gerado por *G4 Lead Scorer* · Powered by Lucas de Paula" },
    ],
  });

  return blocks;
}

// ── Evening ───────────────────────────────────────────────────────────────────

export function buildEveningBlocks(deals: ScoredDeal[]): object[] {
  const active   = deals.filter((d) => d.deal_stage === "Engaging" || d.deal_stage === "Prospecting");
  const won      = deals.filter((d) => d.deal_stage === "Won");
  const lost     = deals.filter((d) => d.deal_stage === "Lost");
  const avgScore = active.length > 0
    ? Math.round(active.reduce((s, d) => s + d.score, 0) / active.length)
    : 0;
  const winRate  = (won.length + lost.length) > 0
    ? Math.round((won.length / (won.length + lost.length)) * 100)
    : 0;
  const top5Zombies = deals
    .filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 90)
    .sort((a, b) => b.days_in_stage - a.days_in_stage)
    .slice(0, 5);
  const atRisk = active.filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 30 && d.days_in_stage <= 90).length;

  const blocks: object[] = [
    {
      type: "header",
      text: { type: "plain_text", text: "🌙 Lead Scorer — Resumo do Pipeline", emoji: true },
    },
    {
      type: "context",
      elements: [{ type: "mrkdwn", text: `📅 ${todayBR()}` }],
    },
    {
      type: "section",
      fields: [
        { type: "mrkdwn", text: `*Deals ativos*\n${active.length}` },
        { type: "mrkdwn", text: `*🏆 Won (total)*\n${won.length}` },
        { type: "mrkdwn", text: `*❌ Lost (total)*\n${lost.length}` },
        { type: "mrkdwn", text: `*📊 Win rate*\n${winRate}%` },
        { type: "mrkdwn", text: `*⭐ Score médio*\n${avgScore}` },
        { type: "mrkdwn", text: `*⚠️ Em risco (31–90d)*\n${atRisk}` },
      ],
    },
    { type: "divider" },
    {
      type: "section",
      text: { type: "mrkdwn", text: "*💀 Top 5 Zumbis para revisar ou encerrar:*" },
    },
  ];

  if (top5Zombies.length === 0) {
    blocks.push({
      type: "section",
      text: { type: "mrkdwn", text: "✅ Nenhum zumbi ativo. Pipeline com boa saúde!" },
    });
  } else {
    top5Zombies.forEach((deal, i) => {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: [
            `*${i + 1}. ${deal.account || "Sem conta"}* — ${deal.product}`,
            `💀 *${deal.days_in_stage} dias* parado | Score: ${deal.score} | 👤 ${deal.sales_agent}`,
          ].join("\n"),
        },
      });
    });
  }

  blocks.push({ type: "divider" });
  blocks.push({
    type: "context",
    elements: [
      { type: "mrkdwn", text: "Gerado por *G4 Lead Scorer* · Powered by Lucas de Paula" },
    ],
  });

  return blocks;
}

// ── Send ──────────────────────────────────────────────────────────────────────

export async function sendSlackBlocks(webhookUrl: string, blocks: object[]): Promise<void> {
  const res = await fetch(webhookUrl, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ blocks }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Slack retornou ${res.status}: ${text}`);
  }
}
