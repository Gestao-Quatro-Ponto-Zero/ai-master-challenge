module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[project]/utils/deal-explanation.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getDealScoreExplanation",
    ()=>getDealScoreExplanation
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$openai$2f$index$2e$mjs__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/openai/index.mjs [app-route] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$openai$2f$client$2e$mjs__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__OpenAI__as__default$3e$__ = __turbopack_context__.i("[project]/node_modules/openai/client.mjs [app-route] (ecmascript) <export OpenAI as default>");
;
function readApiKey() {
    const key = process.env.OPENAI_API_KEY?.trim();
    return key ? key : null;
}
function buildFactorSummary(factor, fallback) {
    if (!factor) {
        return fallback;
    }
    return `${factor.label}: ${factor.reason}`;
}
function scoreTier(score) {
    if (score >= 67) return "Alta";
    if (score >= 45) return "Media";
    return "Baixa";
}
function serializeFactors(factors) {
    return factors.map((factor)=>{
        return `- ${factor.label}: ${factor.reason}`;
    }).join("\n");
}
function normalizeFactorsForNarrative(input) {
    const positiveFactors = input.topPositiveFactors.filter((factor)=>factor.signedImpact > 0);
    // A clipped max score can still carry tiny negative factors. Hide negligible
    // negatives to keep the explanation aligned with the displayed score.
    const minNegativeImpact = input.score >= 99 ? 0.25 : 0.05;
    const negativeFactors = input.topNegativeFactors.filter((factor)=>factor.signedImpact < -minNegativeImpact);
    return {
        positiveFactors,
        negativeFactors
    };
}
function coerceModelExplanation(raw) {
    if (!raw) {
        return {};
    }
    try {
        return JSON.parse(raw);
    } catch  {
        return {};
    }
}
function extractJsonObject(raw) {
    const firstBrace = raw.indexOf("{");
    const lastBrace = raw.lastIndexOf("}");
    if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) {
        return null;
    }
    return raw.slice(firstBrace, lastBrace + 1);
}
function parseModelExplanation(raw) {
    const direct = coerceModelExplanation(raw);
    if (direct.summary || direct.nextAction) {
        return direct;
    }
    if (!raw) {
        return {};
    }
    const extracted = extractJsonObject(raw);
    if (!extracted) {
        return {};
    }
    return coerceModelExplanation(extracted);
}
function buildPrompt(input) {
    const narrativeFactors = normalizeFactorsForNarrative(input);
    const positiveFactors = serializeFactors(narrativeFactors.positiveFactors);
    const negativeFactors = serializeFactors(narrativeFactors.negativeFactors);
    const riskInstruction = narrativeFactors.negativeFactors.length > 0 ? "- Mencione pontos positivos e riscos quando ambos existirem." : "- Não mencione riscos ou pontos negativos quando nenhum for informado nos principais fatores negativos.";
    return `Contexto:\n- Objetivo do app: ajudar vendedores a decidir onde focar em seguida.\n- Objetivo da explicação: justificativa objetiva e personalizada para o score deste negócio.\n\nResumo do negócio:\n- Vendedor: ${input.salesAgent}\n- Produto: ${input.product}\n- Conta: ${input.account}\n- Etapa do negócio: ${input.dealStage}\n- Faixa de prioridade: ${scoreTier(input.score)}\n\nPrincipais fatores positivos de score (linguagem simples):\n${positiveFactors || "- Nenhum"}\n\nPrincipais fatores negativos de score (linguagem simples):\n${negativeFactors || "- Nenhum"}\n\nRequisitos de saida:\n- Retorne apenas JSON valido com as chaves: summary, nextAction.\n- summary: 2-4 frases, clara e objetiva, adaptada ao contexto deste vendedor/negócio.\n- Comece direto pelos fatores principais e contexto; não abra com repetição de metadados.\n- Não mencione o ID da oportunidade nem o score numerico na resposta. Mencionar o nome da conta/empresa e permitido.\n- nextAction: uma ação especifica e pratica para o vendedor.\n- Não inclua mecanicas internas de score (IDs de criterio, impactos, pesos, multiplicadores, formulas ou metadados numericos).\n${riskInstruction}`;
}
function buildFallbackResponse(input) {
    const strongestPositive = input.topPositiveFactors[0];
    const strongestNegative = input.topNegativeFactors[0];
    return {
        summary: `Esta e uma explicação provisoria da IA para ${input.opportunityId}. O score atual e ${input.score}. Sinal positivo mais forte: ${buildFactorSummary(strongestPositive, "Nenhum sinal positivo foi identificado.")} Strongest risk signal: ${buildFactorSummary(strongestNegative, "Nenhum sinal de risco relevante foi identificado.")}`,
        nextAction: "Confirme o cronograma de compra na proxima conversa e revalide os criterios de decisao antes de comprometer o forecast.",
        generatedAt: new Date().toISOString(),
        source: "placeholder"
    };
}
async function getDealScoreExplanation(input) {
    const apiKey = readApiKey();
    if (!apiKey) {
        return buildFallbackResponse(input);
    }
    const client = new __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$openai$2f$client$2e$mjs__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$export__OpenAI__as__default$3e$__["default"]({
        apiKey
    });
    const model = process.env.OPENAI_MODEL?.trim() || "gpt-5-nano";
    try {
        const response = await client.responses.create({
            model,
            instructions: "Voce e um assistente de enablement de vendas para um app de priorização de leads em CRM. Produza uma explicação objetiva, concisa e personalizada sobre por que um negócio recebeu seu score. Fale diretamente com o vendedor em portugues brasileiro. Baseie sua resposta apenas em fatos e fatores fornecidos. Não invente dados. Não mencione pontos negativos quando nenhum for fornecido no contexto de entrada. Nunca exponha mecanicas internas de score como IDs de criterio, impactos, pesos, multiplicadores, formulas ou calculos brutos. Não mencione o ID da oportunidade nem o score numerico. Mencionar o nome da conta/empresa e permitido. Retorne apenas JSON valido.",
            input: buildPrompt(input)
        });
        const parsed = parseModelExplanation(response.output_text);
        const summary = parsed.summary?.trim();
        const nextAction = parsed.nextAction?.trim();
        if (!summary || !nextAction) {
            return buildFallbackResponse(input);
        }
        return {
            summary,
            nextAction,
            generatedAt: new Date().toISOString(),
            source: "openai"
        };
    } catch (error) {
        console.error("Falha ao gerar explicação com OpenAI", error);
        return buildFallbackResponse(input);
    }
}
}),
"[project]/app/api/deals/explanation/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "POST",
    ()=>POST
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$deal$2d$explanation$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/utils/deal-explanation.ts [app-route] (ecmascript)");
;
;
function isValidPayload(body) {
    if (!body || typeof body !== "object") {
        return false;
    }
    const candidate = body;
    return typeof candidate.opportunityId === "string" && typeof candidate.salesAgent === "string" && typeof candidate.product === "string" && typeof candidate.account === "string" && typeof candidate.dealStage === "string" && typeof candidate.score === "number" && Array.isArray(candidate.topPositiveFactors) && Array.isArray(candidate.topNegativeFactors);
}
async function POST(request) {
    try {
        const body = await request.json();
        if (!isValidPayload(body)) {
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                error: "Payload de solicitação de explicação invalido."
            }, {
                status: 400
            });
        }
        const explanation = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$deal$2d$explanation$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["getDealScoreExplanation"])(body);
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json(explanation);
    } catch  {
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: "Não foi possivel gerar a explicação."
        }, {
            status: 500
        });
    }
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__302239ee._.js.map