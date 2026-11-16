/** Deterministic check for the narrative sanitizer (leaked tool-call markup scrub). */
import { sanitizeNarrative } from "../src/engine/agent";

let pass = 0;
let fail = 0;
function check(name: string, got: string, wantIncludes: string[], wantExcludes: string[]) {
  const okIn = wantIncludes.every((s) => got.includes(s));
  const okOut = wantExcludes.every((s) => !got.includes(s));
  if (okIn && okOut) {
    pass++;
  } else {
    fail++;
    console.log(`FAIL ${name}\n  got: ${JSON.stringify(got)}`);
  }
}

// (a) DeepSeek unicode tool-call tokens leaking after prose (the image #7 case)
const deepseek =
  "Tickets have spiked sharply and CSAT cratered.\n\n" +
  "<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function<｜tool▁sep｜>make_chart\n```json\n{\"type\":\"area\"}\n```<｜tool▁call▁end｜><｜tool▁calls▁end｜>";
check("deepseek-tokens", sanitizeNarrative(deepseek), ["Tickets have spiked sharply and CSAT cratered."], ["make_chart", "tool", "json", "｜"]);

// (b) Anthropic-style invoke/parameter XML leaking after prose
const anthropic =
  "All three suites are declining.\n\n<invoke name=\"make_chart\">\n<parameter name=\"chart_type\">area</parameter>\n<parameter name=\"data\">[{\"x\":1}]</parameter>\n</invoke>";
check("anthropic-xml", sanitizeNarrative(anthropic), ["All three suites are declining."], ["make_chart", "invoke", "parameter", "chart_type"]);

// (c) clean prose passes through untouched (incl. a legit "<" comparison)
const clean = "Enterprise ARR is $134M; any account with health < 40 is at risk.";
check("clean-passthrough", sanitizeNarrative(clean), ["health < 40 is at risk", "$134M"], ["undefined"]);

// (d) whole content is a leaked call → empty (forces the tool_choice:none re-narration)
const onlyCall = "<｜tool▁calls▁begin｜>function<｜tool▁sep｜>make_chart";
check("only-call-empties", sanitizeNarrative(onlyCall) === "" ? "EMPTY" : sanitizeNarrative(onlyCall), ["EMPTY"], ["make_chart"]);

console.log(fail === 0 ? `SANITIZE OK — ${pass} checks passed` : `SANITIZE FAILED — ${fail} failed, ${pass} passed`);
process.exit(fail === 0 ? 0 : 1);
