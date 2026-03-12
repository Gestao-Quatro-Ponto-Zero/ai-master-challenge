module.exports = [
"[project]/app/favicon.ico.mjs { IMAGE => \"[project]/app/favicon.ico (static in ecmascript, tag client)\" } [app-rsc] (structured image object, ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/favicon.ico.mjs { IMAGE => \"[project]/app/favicon.ico (static in ecmascript, tag client)\" } [app-rsc] (structured image object, ecmascript)"));
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[project]/app/layout.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/layout.tsx [app-rsc] (ecmascript)"));
}),
"[externals]/node:fs/promises [external] (node:fs/promises, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("node:fs/promises", () => require("node:fs/promises"));

module.exports = mod;
}),
"[externals]/node:path [external] (node:path, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("node:path", () => require("node:path"));

module.exports = mod;
}),
"[project]/utils/crm-data.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getAccountsRows",
    ()=>getAccountsRows,
    "getProductRows",
    ()=>getProductRows,
    "getSalesPipelineRows",
    ()=>getSalesPipelineRows
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$fs$2f$promises__$5b$external$5d$__$28$node$3a$fs$2f$promises$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/node:fs/promises [external] (node:fs/promises, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$path__$5b$external$5d$__$28$node$3a$path$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/node:path [external] (node:path, cjs)");
;
;
const DOCS_DIR = __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$path__$5b$external$5d$__$28$node$3a$path$2c$__cjs$29$__["default"].join(process.cwd(), "public", "docs");
function parseCsvLine(line) {
    const values = [];
    let current = "";
    let insideQuotes = false;
    for(let index = 0; index < line.length; index += 1){
        const char = line[index];
        if (char === '"') {
            const nextChar = line[index + 1];
            if (insideQuotes && nextChar === '"') {
                current += '"';
                index += 1;
                continue;
            }
            insideQuotes = !insideQuotes;
            continue;
        }
        if (char === "," && !insideQuotes) {
            values.push(current.trim());
            current = "";
            continue;
        }
        current += char;
    }
    values.push(current.trim());
    return values;
}
function splitCsvRows(fileContents) {
    const [headerLine, ...lineRows] = fileContents.split(/\r?\n/).map((line)=>line.trim()).filter(Boolean);
    if (!headerLine) {
        return {
            headers: [],
            rows: []
        };
    }
    return {
        headers: parseCsvLine(headerLine),
        rows: lineRows.map(parseCsvLine)
    };
}
function ensureHeaders(fileName, actualHeaders, expectedHeaders) {
    const isValid = actualHeaders.length === expectedHeaders.length && expectedHeaders.every((header, index)=>actualHeaders[index] === header);
    if (!isValid) {
        throw new Error(`${fileName} headers do not match expected schema.`);
    }
}
async function getSalesPipelineRows() {
    const fileContents = await (0, __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$fs$2f$promises__$5b$external$5d$__$28$node$3a$fs$2f$promises$2c$__cjs$29$__["readFile"])(__TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$path__$5b$external$5d$__$28$node$3a$path$2c$__cjs$29$__["default"].join(DOCS_DIR, "sales_pipeline.csv"), "utf8");
    const { headers, rows } = splitCsvRows(fileContents);
    ensureHeaders("sales_pipeline.csv", headers, [
        "opportunity_id",
        "sales_agent",
        "product",
        "account",
        "deal_stage",
        "engage_date",
        "close_date",
        "close_value"
    ]);
    return rows.map((row)=>({
            opportunity_id: row[0] ?? "",
            sales_agent: row[1] ?? "",
            product: row[2] ?? "",
            account: row[3] ?? "",
            deal_stage: row[4] ?? "",
            engage_date: row[5] ?? "",
            close_date: row[6] || null,
            close_value: row[7] || null
        }));
}
async function getAccountsRows() {
    const fileContents = await (0, __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$fs$2f$promises__$5b$external$5d$__$28$node$3a$fs$2f$promises$2c$__cjs$29$__["readFile"])(__TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$path__$5b$external$5d$__$28$node$3a$path$2c$__cjs$29$__["default"].join(DOCS_DIR, "accounts.csv"), "utf8");
    const { headers, rows } = splitCsvRows(fileContents);
    ensureHeaders("accounts.csv", headers, [
        "account",
        "sector",
        "year_established",
        "revenue",
        "employees",
        "office_location",
        "subsidiary_of"
    ]);
    return rows.map((row)=>({
            account: row[0] ?? "",
            sector: row[1] ?? "",
            revenue: row[3] ?? "0"
        }));
}
async function getProductRows() {
    const fileContents = await (0, __TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$fs$2f$promises__$5b$external$5d$__$28$node$3a$fs$2f$promises$2c$__cjs$29$__["readFile"])(__TURBOPACK__imported__module__$5b$externals$5d2f$node$3a$path__$5b$external$5d$__$28$node$3a$path$2c$__cjs$29$__["default"].join(DOCS_DIR, "products.csv"), "utf8");
    const { headers, rows } = splitCsvRows(fileContents);
    ensureHeaders("products.csv", headers, [
        "product",
        "series",
        "sales_price"
    ]);
    return rows.map((row)=>({
            product: row[0] ?? "",
            sales_price: row[2] ?? "0"
        }));
}
}),
"[project]/utils/deal-score.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "calculateDealScore",
    ()=>calculateDealScore,
    "calculateDealScoreBreakdown",
    ()=>calculateDealScoreBreakdown
]);
function calculateDealScoreBreakdown(input) {
    const { deal, salesPipeline, accounts, products } = input;
    const asOfDate = input.asOfDate ? new Date(input.asOfDate) : new Date();
    const WEIGHTS = {
        criterion1: 1.35,
        criterion2: -1.0,
        criterion3: -0.85,
        criterion4: 1.1,
        criterion5: 1.25,
        criterion6: 0.9,
        criterion7: 0.8,
        criterion8: 1.15,
        criterion9: 1.0
    };
    const normalize = (value)=>(value ?? "").trim().toLowerCase();
    const normalizeProduct = (value)=>normalize(value).replace(/\s+/g, "");
    const parseNumber = (value)=>{
        const parsed = typeof value === "number" ? value : Number(value ?? 0);
        return Number.isFinite(parsed) ? parsed : 0;
    };
    const parseDate = (value)=>{
        if (!value) return null;
        const parsed = new Date(value);
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    };
    const daysBetween = (startDate, endDate)=>{
        if (!startDate || !endDate) return null;
        const diffMs = endDate.getTime() - startDate.getTime();
        if (!Number.isFinite(diffMs)) return null;
        return Math.max(0, diffMs / 86_400_000);
    };
    const mean = (values)=>{
        if (values.length === 0) return 0;
        const total = values.reduce((sum, value)=>sum + value, 0);
        return total / values.length;
    };
    const ratio = (numerator, denominator)=>{
        if (denominator <= 0 || !Number.isFinite(denominator)) return 1;
        if (!Number.isFinite(numerator)) return 1;
        const raw = numerator / denominator;
        if (!Number.isFinite(raw) || raw <= 0) return 1;
        return raw;
    };
    const inverse = (multiple)=>{
        if (!Number.isFinite(multiple) || multiple <= 0) return 1;
        return 1 / multiple;
    };
    const accountByName = new Map(accounts.map((account)=>[
            normalize(account.account),
            account
        ]));
    const priceByProduct = new Map(products.map((product)=>[
            normalizeProduct(product.product),
            parseNumber(product.sales_price)
        ]));
    const isClosedDeal = (row)=>{
        const stage = normalize(row.deal_stage);
        return stage === "won" || stage === "lost";
    };
    const isWonDeal = (row)=>normalize(row.deal_stage) === "won";
    const historicalClosedDeals = salesPipeline.filter((row)=>isClosedDeal(row) && parseDate(row.close_date) !== null);
    const historicalWonDeals = historicalClosedDeals.filter(isWonDeal);
    const winRate = (rows)=>{
        if (rows.length === 0) return 0;
        const wins = rows.filter(isWonDeal).length;
        return wins / rows.length;
    };
    const cycleDays = (row)=>daysBetween(parseDate(row.engage_date), parseDate(row.close_date));
    const cycleDaysForRows = (rows)=>rows.map(cycleDays).filter((value)=>value !== null && Number.isFinite(value));
    const currentAgent = normalize(deal.sales_agent);
    const currentProduct = normalizeProduct(deal.product);
    const currentAccount = normalize(deal.account);
    const currentSector = normalize(accountByName.get(currentAccount)?.sector);
    // CRITERION 1
    const closedByAgent = historicalClosedDeals.filter((row)=>normalize(row.sales_agent) === currentAgent);
    const closedByAgentAndProduct = closedByAgent.filter((row)=>normalizeProduct(row.product) === currentProduct);
    const productWinRateByAgent = winRate(closedByAgentAndProduct);
    const otherProductsByAgent = Array.from(new Set(closedByAgent.map((row)=>normalizeProduct(row.product)).filter((productKey)=>productKey !== currentProduct)));
    const averageOtherProductWinRate = mean(otherProductsByAgent.map((productKey)=>{
        const rows = closedByAgent.filter((row)=>normalizeProduct(row.product) === productKey);
        return winRate(rows);
    }));
    const criterion1Multiple = ratio(productWinRateByAgent, averageOtherProductWinRate);
    // CRITERION 2
    const closedByProduct = historicalClosedDeals.filter((row)=>normalizeProduct(row.product) === currentProduct);
    const closedByOtherProducts = historicalClosedDeals.filter((row)=>normalizeProduct(row.product) !== currentProduct);
    const avgDaysProduct = mean(cycleDaysForRows(closedByProduct));
    const avgDaysOtherProducts = mean(cycleDaysForRows(closedByOtherProducts));
    const criterion2Multiple = ratio(avgDaysProduct, avgDaysOtherProducts);
    // CRITERION 3
    const closedByAccount = historicalClosedDeals.filter((row)=>normalize(row.account) === currentAccount);
    const closedByOtherAccounts = historicalClosedDeals.filter((row)=>normalize(row.account) !== currentAccount);
    const avgDaysAccount = mean(cycleDaysForRows(closedByAccount));
    const avgDaysOtherAccounts = mean(cycleDaysForRows(closedByOtherAccounts));
    const criterion3Multiple = ratio(avgDaysAccount, avgDaysOtherAccounts);
    // CRITERION 4
    const wonInSector = historicalWonDeals.filter((row)=>{
        const accountSector = normalize(accountByName.get(normalize(row.account))?.sector);
        return accountSector === currentSector;
    });
    const winsInSectorForProduct = wonInSector.filter((row)=>normalizeProduct(row.product) === currentProduct).length;
    const frequencyProductInSector = ratio(winsInSectorForProduct, wonInSector.length || 1);
    const otherProductsInSector = Array.from(new Set(wonInSector.map((row)=>normalizeProduct(row.product)).filter((productKey)=>productKey !== currentProduct)));
    const avgOtherProductFrequencyInSector = mean(otherProductsInSector.map((productKey)=>{
        const wins = wonInSector.filter((row)=>normalizeProduct(row.product) === productKey).length;
        return ratio(wins, wonInSector.length || 1);
    }));
    const criterion4Multiple = ratio(frequencyProductInSector, avgOtherProductFrequencyInSector);
    // CRITERION 5
    const allAgentClosedDeals = historicalClosedDeals.filter((row)=>normalize(row.sales_agent) === currentAgent);
    const recentStart = new Date(asOfDate);
    recentStart.setMonth(recentStart.getMonth() - 3);
    const recentAgentClosedDeals = allAgentClosedDeals.filter((row)=>{
        const closeDate = parseDate(row.close_date);
        return closeDate !== null && closeDate >= recentStart && closeDate <= asOfDate;
    });
    const agentRecentWinRate = winRate(recentAgentClosedDeals);
    const agentOverallWinRate = winRate(allAgentClosedDeals);
    const criterion5Multiple = ratio(agentRecentWinRate, agentOverallWinRate);
    // CRITERION 6 (inverse multiple)
    const dealValue = Math.max(parseNumber(deal.close_value), priceByProduct.get(currentProduct) ?? 0);
    const revenuesOfSimilarWonAccounts = historicalWonDeals.filter((row)=>{
        const accountSector = normalize(accountByName.get(normalize(row.account))?.sector);
        return accountSector === currentSector;
    }).map((row)=>parseNumber(accountByName.get(normalize(row.account))?.revenue)).filter((revenue)=>revenue > 0);
    const avgRevenueSimilarWonAccounts = mean(revenuesOfSimilarWonAccounts);
    const criterion6Multiple = ratio(dealValue, avgRevenueSimilarWonAccounts);
    // CRITERION 7 (inverse multiple)
    const openDeals = salesPipeline.filter((row)=>!isClosedDeal(row));
    const openByAgentCount = openDeals.filter((row)=>normalize(row.sales_agent) === currentAgent).length;
    const openDealsByAgentMap = new Map();
    for (const row of openDeals){
        const agent = normalize(row.sales_agent);
        openDealsByAgentMap.set(agent, (openDealsByAgentMap.get(agent) ?? 0) + 1);
    }
    const avgOpenDealsByAgent = mean(Array.from(openDealsByAgentMap.values()));
    const criterion7Multiple = ratio(openByAgentCount, avgOpenDealsByAgent);
    // CRITERION 8 (inverse multiple)
    // Approximation: the CSV has no stage-entry timestamp, so we use deal age since engage_date.
    const currentAgeDays = daysBetween(parseDate(deal.engage_date), asOfDate) ?? 0;
    const historicalAverageCycleDays = mean(cycleDaysForRows(historicalClosedDeals));
    const criterion8Multiple = ratio(currentAgeDays, historicalAverageCycleDays);
    // CRITERION 9
    const companyWonCount = historicalWonDeals.filter((row)=>normalize(row.account) === currentAccount).length;
    const wonCountByCompany = new Map();
    for (const row of historicalWonDeals){
        const account = normalize(row.account);
        wonCountByCompany.set(account, (wonCountByCompany.get(account) ?? 0) + 1);
    }
    const otherCompanyWonCounts = Array.from(wonCountByCompany.entries()).filter(([account])=>account !== currentAccount).map(([, count])=>count);
    const avgOtherCompanyWonCount = mean(otherCompanyWonCounts);
    const criterion9Multiple = ratio(companyWonCount, avgOtherCompanyWonCount);
    const factors = [
        {
            criterion: "criterion1",
            label: "Rep fit for this product",
            weight: WEIGHTS.criterion1,
            multiple: criterion1Multiple,
            signedImpact: WEIGHTS.criterion1 * (criterion1Multiple - 1),
            reason: "Compares this rep's win rate on the product against their win rate on other products."
        },
        {
            criterion: "criterion2",
            label: "Product sales-cycle speed",
            weight: WEIGHTS.criterion2,
            multiple: criterion2Multiple,
            signedImpact: WEIGHTS.criterion2 * (criterion2Multiple - 1),
            reason: "Compares average time-to-close for this product against other products."
        },
        {
            criterion: "criterion3",
            label: "Account sales-cycle speed",
            weight: WEIGHTS.criterion3,
            multiple: criterion3Multiple,
            signedImpact: WEIGHTS.criterion3 * (criterion3Multiple - 1),
            reason: "Compares this account's average time-to-close against other accounts."
        },
        {
            criterion: "criterion4",
            label: "Product demand in sector",
            weight: WEIGHTS.criterion4,
            multiple: criterion4Multiple,
            signedImpact: WEIGHTS.criterion4 * (criterion4Multiple - 1),
            reason: "Measures how often this product wins in the account's sector versus alternatives."
        },
        {
            criterion: "criterion5",
            label: "Rep recent momentum",
            weight: WEIGHTS.criterion5,
            multiple: criterion5Multiple,
            signedImpact: WEIGHTS.criterion5 * (criterion5Multiple - 1),
            reason: "Compares rep win rate in the last 3 months against their long-term baseline."
        },
        {
            criterion: "criterion6",
            label: "Deal size vs similar accounts",
            weight: WEIGHTS.criterion6,
            multiple: criterion6Multiple,
            signedImpact: WEIGHTS.criterion6 * (inverse(criterion6Multiple) - 1),
            reason: "Larger-than-typical deals in similar sectors are treated as harder to close."
        },
        {
            criterion: "criterion7",
            label: "Rep workload balance",
            weight: WEIGHTS.criterion7,
            multiple: criterion7Multiple,
            signedImpact: WEIGHTS.criterion7 * (inverse(criterion7Multiple) - 1),
            reason: "Compares the rep's open-deal count against the team average."
        },
        {
            criterion: "criterion8",
            label: "Deal freshness",
            weight: WEIGHTS.criterion8,
            multiple: criterion8Multiple,
            signedImpact: WEIGHTS.criterion8 * (inverse(criterion8Multiple) - 1),
            reason: "Older open deals are penalized compared with historical average cycle time."
        },
        {
            criterion: "criterion9",
            label: "Account historical wins",
            weight: WEIGHTS.criterion9,
            multiple: criterion9Multiple,
            signedImpact: WEIGHTS.criterion9 * (criterion9Multiple - 1),
            reason: "Rewards accounts where the company has won more often than average."
        }
    ];
    const rawScore = factors.reduce((sum, factor)=>sum + factor.signedImpact, 0);
    const scaledScore = 50 + rawScore * 15;
    const finalScore = Math.max(0, Math.min(100, Number(scaledScore.toFixed(2))));
    const topPositiveFactors = factors.filter((factor)=>factor.signedImpact > 0).sort((left, right)=>right.signedImpact - left.signedImpact).slice(0, 3);
    const topNegativeFactors = factors.filter((factor)=>factor.signedImpact < 0).sort((left, right)=>left.signedImpact - right.signedImpact).slice(0, 3);
    return {
        finalScore,
        factors,
        topPositiveFactors,
        topNegativeFactors
    };
}
function calculateDealScore(input) {
    return calculateDealScoreBreakdown(input).finalScore;
}
}),
"[project]/app/pipeline/pipeline-deals-list.tsx [app-rsc] (client reference proxy) <module evaluation>", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PipelineDealsList",
    ()=>PipelineDealsList
]);
// This file is generated by next-core EcmascriptClientReferenceModule.
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-server-dom-turbopack-server.js [app-rsc] (ecmascript)");
;
const PipelineDealsList = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["registerClientReference"])(function() {
    throw new Error("Attempted to call PipelineDealsList() from the server but PipelineDealsList is on the client. It's not possible to invoke a client function from the server, it can only be rendered as a Component or passed to props of a Client Component.");
}, "[project]/app/pipeline/pipeline-deals-list.tsx <module evaluation>", "PipelineDealsList");
}),
"[project]/app/pipeline/pipeline-deals-list.tsx [app-rsc] (client reference proxy)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PipelineDealsList",
    ()=>PipelineDealsList
]);
// This file is generated by next-core EcmascriptClientReferenceModule.
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-server-dom-turbopack-server.js [app-rsc] (ecmascript)");
;
const PipelineDealsList = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$server$2d$dom$2d$turbopack$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["registerClientReference"])(function() {
    throw new Error("Attempted to call PipelineDealsList() from the server but PipelineDealsList is on the client. It's not possible to invoke a client function from the server, it can only be rendered as a Component or passed to props of a Client Component.");
}, "[project]/app/pipeline/pipeline-deals-list.tsx", "PipelineDealsList");
}),
"[project]/app/pipeline/pipeline-deals-list.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

var __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$pipeline$2f$pipeline$2d$deals$2d$list$2e$tsx__$5b$app$2d$rsc$5d$__$28$client__reference__proxy$29$__$3c$module__evaluation$3e$__ = __turbopack_context__.i("[project]/app/pipeline/pipeline-deals-list.tsx [app-rsc] (client reference proxy) <module evaluation>");
var __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$pipeline$2f$pipeline$2d$deals$2d$list$2e$tsx__$5b$app$2d$rsc$5d$__$28$client__reference__proxy$29$__ = __turbopack_context__.i("[project]/app/pipeline/pipeline-deals-list.tsx [app-rsc] (client reference proxy)");
;
__turbopack_context__.n(__TURBOPACK__imported__module__$5b$project$5d2f$app$2f$pipeline$2f$pipeline$2d$deals$2d$list$2e$tsx__$5b$app$2d$rsc$5d$__$28$client__reference__proxy$29$__);
}),
"[project]/app/pipeline/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>PipelinePage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$headers$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/headers.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/client/app-dir/link.react-server.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$api$2f$navigation$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/next/dist/api/navigation.react-server.js [app-rsc] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$components$2f$navigation$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/client/components/navigation.react-server.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$crm$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/utils/crm-data.ts [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$deal$2d$score$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/utils/deal-score.ts [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$app$2f$pipeline$2f$pipeline$2d$deals$2d$list$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/app/pipeline/pipeline-deals-list.tsx [app-rsc] (ecmascript)");
;
;
;
;
;
;
;
const SALES_AGENT_COOKIE = "lead-scorer-sales-agent";
const DEFAULT_PAGE_SIZE = 8;
const MIN_PAGE_SIZE = 1;
const MAX_PAGE_SIZE = 100;
function normalize(value) {
    return value.trim().toLowerCase();
}
function parsePositiveInteger(value) {
    if (!value) return null;
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed <= 0) return null;
    return parsed;
}
function parseStagePriority(value) {
    if (value === "engaging" || value === "prospecting") {
        return value;
    }
    return "none";
}
function stageOrder(stage, stagePriority) {
    const normalizedStage = normalize(stage);
    if (stagePriority === "none") return 0;
    if (stagePriority === "engaging") {
        return normalizedStage === "engaging" ? 0 : 1;
    }
    return normalizedStage === "prospecting" ? 0 : 1;
}
function buildPipelineHref(input) {
    const params = new URLSearchParams();
    if (input.stagePriority !== "none") {
        params.set("prioritize", input.stagePriority);
    }
    if (input.page && input.page > 1) {
        params.set("page", String(input.page));
    }
    if (input.pageSize && input.pageSize !== DEFAULT_PAGE_SIZE) {
        params.set("pageSize", String(input.pageSize));
    }
    const query = params.toString();
    return query ? `/pipeline?${query}` : "/pipeline";
}
async function PipelinePage({ searchParams }) {
    const cookieStore = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$headers$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["cookies"])();
    const selectedSalesAgent = cookieStore.get(SALES_AGENT_COOKIE)?.value;
    if (!selectedSalesAgent) {
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$components$2f$navigation$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["redirect"])("/");
    }
    const params = await searchParams;
    const stagePriority = parseStagePriority(params?.prioritize);
    const pageSize = Math.min(MAX_PAGE_SIZE, Math.max(MIN_PAGE_SIZE, parsePositiveInteger(params?.pageSize) ?? DEFAULT_PAGE_SIZE));
    const [salesPipeline, accounts, products] = await Promise.all([
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$crm$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getSalesPipelineRows"])(),
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$crm$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getAccountsRows"])(),
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$crm$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getProductRows"])()
    ]);
    const selectedAgentDeals = salesPipeline.filter((row)=>normalize(row.sales_agent) === normalize(selectedSalesAgent));
    const openAgentDeals = selectedAgentDeals.filter((row)=>{
        const stage = normalize(row.deal_stage);
        return stage === "engaging" || stage === "prospecting";
    });
    const rankedDeals = openAgentDeals.map((deal)=>{
        const scoreBreakdown = (0, __TURBOPACK__imported__module__$5b$project$5d2f$utils$2f$deal$2d$score$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["calculateDealScoreBreakdown"])({
            deal,
            salesPipeline,
            accounts,
            products
        });
        return {
            ...deal,
            score: scoreBreakdown.finalScore,
            scoreBreakdown
        };
    }).sort((left, right)=>{
        const stageDiff = stageOrder(left.deal_stage, stagePriority) - stageOrder(right.deal_stage, stagePriority);
        if (stageDiff !== 0) {
            return stageDiff;
        }
        if (right.score !== left.score) {
            return right.score - left.score;
        }
        return left.opportunity_id.localeCompare(right.opportunity_id);
    });
    const totalDeals = rankedDeals.length;
    const totalPages = Math.max(1, Math.ceil(totalDeals / pageSize));
    const requestedPage = parsePositiveInteger(params?.page) ?? 1;
    const currentPage = Math.min(requestedPage, totalPages);
    const startIndex = (currentPage - 1) * pageSize;
    const paginatedDeals = rankedDeals.slice(startIndex, startIndex + pageSize);
    const paginatedDealsWithViewModel = paginatedDeals.map((deal, index)=>({
            opportunityId: deal.opportunity_id,
            salesAgent: deal.sales_agent,
            product: deal.product,
            account: deal.account,
            stage: deal.deal_stage,
            score: deal.score,
            rank: startIndex + index + 1,
            topPositiveFactors: deal.scoreBreakdown.topPositiveFactors,
            topNegativeFactors: deal.scoreBreakdown.topNegativeFactors
        }));
    const activePriorityLabel = stagePriority === "none" ? "Score only" : stagePriority === "engaging" ? "Engaging first" : "Prospecting first";
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
        className: "min-h-screen bg-[linear-gradient(180deg,#f4ede2,#efe7db)] px-6 py-10 text-stone-900 sm:px-10 lg:px-16",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "mx-auto max-w-6xl space-y-8",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("header", {
                    className: "rounded-4xl border border-stone-900/10 bg-white/85 px-8 py-8 shadow-[0_20px_60px_rgba(76,61,43,0.12)] backdrop-blur",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-sm font-medium uppercase tracking-[0.24em] text-stone-500",
                            children: "Pipeline"
                        }, void 0, false, {
                            fileName: "[project]/app/pipeline/page.tsx",
                            lineNumber: 169,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                                            className: "text-3xl font-semibold tracking-tight text-stone-950",
                                            children: selectedSalesAgent
                                        }, void 0, false, {
                                            fileName: "[project]/app/pipeline/page.tsx",
                                            lineNumber: 174,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "mt-2 max-w-2xl text-sm leading-6 text-stone-600",
                                            children: "Open deals are ranked by score, with optional stage priority forcing Engaging or Prospecting deals to appear first."
                                        }, void 0, false, {
                                            fileName: "[project]/app/pipeline/page.tsx",
                                            lineNumber: 177,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 173,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex flex-wrap items-center gap-3",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                                            className: "inline-flex items-center justify-center rounded-2xl border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-stone-950 hover:text-stone-950",
                                            href: "/",
                                            children: "Switch salesperson"
                                        }, void 0, false, {
                                            fileName: "[project]/app/pipeline/page.tsx",
                                            lineNumber: 183,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "rounded-2xl bg-stone-950 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-stone-50",
                                            children: activePriorityLabel
                                        }, void 0, false, {
                                            fileName: "[project]/app/pipeline/page.tsx",
                                            lineNumber: 189,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 182,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/app/pipeline/page.tsx",
                            lineNumber: 172,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/app/pipeline/page.tsx",
                    lineNumber: 168,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                    className: "rounded-4xl border border-stone-900/10 bg-white/85 p-6 shadow-[0_20px_60px_rgba(76,61,43,0.12)] backdrop-blur sm:p-8",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex flex-wrap items-center gap-3",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-sm font-medium text-stone-600",
                                    children: "Stage priority:"
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 198,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                                    className: `rounded-xl px-3 py-2 text-sm font-medium transition ${stagePriority === "none" ? "bg-stone-950 text-stone-50" : "bg-stone-100 text-stone-700 hover:bg-stone-200"}`,
                                    href: buildPipelineHref({
                                        stagePriority: "none",
                                        page: 1,
                                        pageSize
                                    }),
                                    children: "Score only"
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 199,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                                    className: `rounded-xl px-3 py-2 text-sm font-medium transition ${stagePriority === "engaging" ? "bg-stone-950 text-stone-50" : "bg-stone-100 text-stone-700 hover:bg-stone-200"}`,
                                    href: buildPipelineHref({
                                        stagePriority: "engaging",
                                        page: 1,
                                        pageSize
                                    }),
                                    children: "Engaging first"
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 212,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                                    className: `rounded-xl px-3 py-2 text-sm font-medium transition ${stagePriority === "prospecting" ? "bg-stone-950 text-stone-50" : "bg-stone-100 text-stone-700 hover:bg-stone-200"}`,
                                    href: buildPipelineHref({
                                        stagePriority: "prospecting",
                                        page: 1,
                                        pageSize
                                    }),
                                    children: "Prospecting first"
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 225,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/app/pipeline/page.tsx",
                            lineNumber: 197,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("form", {
                            className: "mt-4 flex flex-wrap items-center gap-3",
                            method: "get",
                            children: [
                                stagePriority !== "none" ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                    name: "prioritize",
                                    type: "hidden",
                                    value: stagePriority
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 242,
                                    columnNumber: 15
                                }, this) : null,
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                    className: "text-sm font-medium text-stone-600",
                                    htmlFor: "pageSize",
                                    children: "Deals per page"
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 244,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                    className: "w-24 rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900",
                                    defaultValue: pageSize,
                                    id: "pageSize",
                                    max: MAX_PAGE_SIZE,
                                    min: MIN_PAGE_SIZE,
                                    name: "pageSize",
                                    type: "number"
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 247,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    className: "rounded-xl bg-stone-950 px-3 py-2 text-sm font-medium text-stone-50 transition hover:bg-stone-800",
                                    type: "submit",
                                    children: "Apply"
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 256,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/app/pipeline/page.tsx",
                            lineNumber: 240,
                            columnNumber: 11
                        }, this),
                        rankedDeals.length === 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "mt-6 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-6 text-sm text-stone-600",
                            children: "No Engaging or Prospecting deals found for this salesperson."
                        }, void 0, false, {
                            fileName: "[project]/app/pipeline/page.tsx",
                            lineNumber: 265,
                            columnNumber: 13
                        }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mt-6 space-y-4",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "text-sm text-stone-600",
                                    children: [
                                        "Showing ",
                                        startIndex + 1,
                                        "-",
                                        Math.min(startIndex + pageSize, totalDeals),
                                        " of ",
                                        totalDeals,
                                        " deals."
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 270,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "overflow-x-auto",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$app$2f$pipeline$2f$pipeline$2d$deals$2d$list$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["PipelineDealsList"], {
                                        deals: paginatedDealsWithViewModel
                                    }, void 0, false, {
                                        fileName: "[project]/app/pipeline/page.tsx",
                                        lineNumber: 275,
                                        columnNumber: 17
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 274,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex flex-wrap items-center gap-2",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                                            "aria-disabled": currentPage === 1,
                                            className: `rounded-xl px-3 py-2 text-sm font-medium transition ${currentPage === 1 ? "pointer-events-none bg-stone-100 text-stone-400" : "bg-stone-950 text-stone-50 hover:bg-stone-800"}`,
                                            href: buildPipelineHref({
                                                stagePriority,
                                                page: Math.max(1, currentPage - 1),
                                                pageSize
                                            }),
                                            children: "Previous"
                                        }, void 0, false, {
                                            fileName: "[project]/app/pipeline/page.tsx",
                                            lineNumber: 279,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "px-2 text-sm text-stone-600",
                                            children: [
                                                "Page ",
                                                currentPage,
                                                " of ",
                                                totalPages
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/app/pipeline/page.tsx",
                                            lineNumber: 294,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$client$2f$app$2d$dir$2f$link$2e$react$2d$server$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["default"], {
                                            "aria-disabled": currentPage === totalPages,
                                            className: `rounded-xl px-3 py-2 text-sm font-medium transition ${currentPage === totalPages ? "pointer-events-none bg-stone-100 text-stone-400" : "bg-stone-950 text-stone-50 hover:bg-stone-800"}`,
                                            href: buildPipelineHref({
                                                stagePriority,
                                                page: Math.min(totalPages, currentPage + 1),
                                                pageSize
                                            }),
                                            children: "Next"
                                        }, void 0, false, {
                                            fileName: "[project]/app/pipeline/page.tsx",
                                            lineNumber: 298,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/app/pipeline/page.tsx",
                                    lineNumber: 278,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/app/pipeline/page.tsx",
                            lineNumber: 269,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/app/pipeline/page.tsx",
                    lineNumber: 196,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/app/pipeline/page.tsx",
            lineNumber: 167,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/app/pipeline/page.tsx",
        lineNumber: 166,
        columnNumber: 5
    }, this);
}
}),
"[project]/app/pipeline/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/app/pipeline/page.tsx [app-rsc] (ecmascript)"));
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__21d41618._.js.map