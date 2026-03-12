module.exports = [
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[project]/app/pipeline/pipeline-deals-list.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PipelineDealsList",
    ()=>PipelineDealsList
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
"use client";
;
;
function scoreTier(score) {
    if (score >= 67) return "High";
    if (score >= 45) return "Medium";
    return "Low";
}
function scoreTierStyles(score) {
    const tier = scoreTier(score);
    if (tier === "High") {
        return "bg-emerald-100 text-emerald-800 border border-emerald-200";
    }
    if (tier === "Medium") {
        return "bg-amber-100 text-amber-800 border border-amber-200";
    }
    return "bg-rose-100 text-rose-800 border border-rose-200";
}
function scoreBadgeStyles(score) {
    const tier = scoreTier(score);
    if (tier === "High") {
        return "bg-emerald-700 text-white";
    }
    if (tier === "Medium") {
        return "bg-amber-500 text-stone-950";
    }
    return "bg-rose-700 text-white";
}
function toFactorChip(factor) {
    return {
        text: factor.label,
        tone: factor.signedImpact >= 0 ? "good" : "risk"
    };
}
async function fetchExplanation(deal) {
    const response = await fetch("/api/deals/explanation", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            opportunityId: deal.opportunityId,
            salesAgent: deal.salesAgent,
            product: deal.product,
            account: deal.account,
            dealStage: deal.stage,
            score: deal.score,
            topPositiveFactors: deal.topPositiveFactors,
            topNegativeFactors: deal.topNegativeFactors
        })
    });
    if (!response.ok) {
        throw new Error("Could not load AI explanation.");
    }
    return await response.json();
}
function PipelineDealsList({ deals }) {
    const initiallyExpanded = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMemo"])(()=>deals.slice(0, 1).map((deal)=>deal.opportunityId), [
        deals
    ]);
    const [expandedIds, setExpandedIds] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(initiallyExpanded);
    const [explanationsById, setExplanationsById] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])({});
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        setExpandedIds(initiallyExpanded);
    }, [
        initiallyExpanded
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        for (const id of expandedIds){
            const deal = deals.find((item)=>item.opportunityId === id);
            if (!deal) continue;
            const explanationState = explanationsById[id];
            if (explanationState && explanationState.status !== "idle") {
                continue;
            }
            setExplanationsById((current)=>({
                    ...current,
                    [id]: {
                        status: "loading"
                    }
                }));
            fetchExplanation(deal).then((data)=>{
                setExplanationsById((current)=>({
                        ...current,
                        [id]: {
                            status: "loaded",
                            data
                        }
                    }));
            }).catch(()=>{
                setExplanationsById((current)=>({
                        ...current,
                        [id]: {
                            status: "error",
                            message: "Explanation service is temporarily unavailable."
                        }
                    }));
            });
        }
    }, [
        deals,
        expandedIds,
        explanationsById
    ]);
    const toggleExplanation = (dealId)=>{
        setExpandedIds((current)=>current.includes(dealId) ? current.filter((id)=>id !== dealId) : [
                ...current,
                dealId
            ]);
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "space-y-4",
        children: deals.map((deal)=>{
            const expanded = expandedIds.includes(deal.opportunityId);
            const explanationState = explanationsById[deal.opportunityId] ?? {
                status: "idle"
            };
            const chips = [
                ...deal.topPositiveFactors.slice(0, 2),
                ...deal.topNegativeFactors.slice(0, 1)
            ].map(toFactorChip);
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                className: "rounded-2xl border border-stone-200 bg-white p-4 shadow-sm",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "space-y-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex flex-wrap items-center gap-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "rounded-full bg-stone-100 px-2 py-1 text-xs font-semibold text-stone-700",
                                                children: [
                                                    "#",
                                                    deal.rank
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                                lineNumber: 169,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: `rounded-full px-2 py-1 text-xs font-semibold ${scoreTierStyles(deal.score)}`,
                                                children: [
                                                    scoreTier(deal.score),
                                                    " priority"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                                lineNumber: 172,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "rounded-full bg-stone-100 px-2 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-stone-700",
                                                children: deal.stage
                                            }, void 0, false, {
                                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                                lineNumber: 177,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                        lineNumber: 168,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                                className: "text-base font-semibold text-stone-900",
                                                children: deal.product
                                            }, void 0, false, {
                                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                                lineNumber: 183,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                className: "text-sm text-stone-600",
                                                children: [
                                                    deal.account || "Unknown account",
                                                    " • ",
                                                    deal.opportunityId
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                                lineNumber: 184,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                        lineNumber: 182,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex flex-wrap gap-2",
                                        children: chips.map((chip, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: `rounded-full px-3 py-1 text-xs font-medium ${chip.tone === "good" ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-800"}`,
                                                children: [
                                                    chip.tone === "good" ? "+" : "-",
                                                    " ",
                                                    chip.text
                                                ]
                                            }, `${deal.opportunityId}-chip-${index}`, true, {
                                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                                lineNumber: 191,
                                                columnNumber: 21
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                        lineNumber: 189,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                lineNumber: 167,
                                columnNumber: 15
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: `rounded-xl px-3 py-2 text-sm font-semibold ${scoreBadgeStyles(deal.score)}`,
                                        children: deal.score
                                    }, void 0, false, {
                                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                        lineNumber: 205,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        "aria-controls": `explanation-${deal.opportunityId}`,
                                        "aria-expanded": expanded,
                                        className: "rounded-xl border border-stone-300 px-3 py-2 text-sm font-medium text-stone-800 transition hover:border-stone-950 hover:text-stone-950",
                                        onClick: ()=>toggleExplanation(deal.opportunityId),
                                        type: "button",
                                        children: expanded ? "Hide why" : "Show why"
                                    }, void 0, false, {
                                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                        lineNumber: 210,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                lineNumber: 204,
                                columnNumber: 15
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                        lineNumber: 166,
                        columnNumber: 13
                    }, this),
                    expanded ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-4 rounded-xl border border-stone-200 bg-stone-50 p-4",
                        id: `explanation-${deal.opportunityId}`,
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-xs font-semibold uppercase tracking-[0.14em] text-stone-500",
                                children: "AI Explanation Preview"
                            }, void 0, false, {
                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                lineNumber: 227,
                                columnNumber: 17
                            }, this),
                            explanationState.status === "loading" || explanationState.status === "idle" ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "mt-2 text-sm text-stone-600",
                                children: "Preparing explanation..."
                            }, void 0, false, {
                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                lineNumber: 232,
                                columnNumber: 19
                            }, this) : null,
                            explanationState.status === "error" ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "mt-2 text-sm text-rose-700",
                                children: explanationState.message
                            }, void 0, false, {
                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                lineNumber: 236,
                                columnNumber: 19
                            }, this) : null,
                            explanationState.status === "loaded" ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-2 space-y-3 text-sm text-stone-700",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        children: explanationState.data.summary
                                    }, void 0, false, {
                                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                        lineNumber: 241,
                                        columnNumber: 21
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "rounded-lg bg-white px-3 py-2 text-stone-800",
                                        children: [
                                            "Next action: ",
                                            explanationState.data.nextAction
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                        lineNumber: 242,
                                        columnNumber: 21
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                                lineNumber: 240,
                                columnNumber: 19
                            }, this) : null
                        ]
                    }, void 0, true, {
                        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                        lineNumber: 223,
                        columnNumber: 15
                    }, this) : null
                ]
            }, deal.opportunityId, true, {
                fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
                lineNumber: 162,
                columnNumber: 11
            }, this);
        })
    }, void 0, false, {
        fileName: "[project]/app/pipeline/pipeline-deals-list.tsx",
        lineNumber: 150,
        columnNumber: 5
    }, this);
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__a726be38._.js.map