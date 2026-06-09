import { spawn } from "child_process";
import path from "path";

export interface ClassificationResult {
  topic_group: string;
  confidence: number;
  probabilities?: Record<string, number>;
}

const PYTHON = process.env.PYTHON_PATH || "python";

const CLASSIFY_SCRIPT = path.join(/* turbopackIgnore: true */ process.cwd(), "ml", "classify.py");

/** Base da API Render — sem barra final e sem sufixo /classify */
function getClassifierApiBase(): string | undefined {
  const raw = process.env.CLASSIFIER_API_URL?.trim();
  if (!raw) return undefined;
  let base = raw.replace(/\/+$/, "");
  if (base.endsWith("/classify")) {
    base = base.slice(0, -"/classify".length);
  }
  return base;
}

const CLASSIFIER_API_BASE = getClassifierApiBase();

async function classifyViaApi(text: string): Promise<ClassificationResult> {
  const base = CLASSIFIER_API_BASE!;
  const url = `${base}/classify`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    cache: "no-store",
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : typeof body.error === "string"
          ? body.error
          : null;
    const hint =
      res.status === 404
        ? ` — confira CLASSIFIER_API_URL (só a base, ex: https://xxx.onrender.com) e GET ${base}/health no Render`
        : "";
    throw new Error(detail ?? `Classificador HTTP ${res.status} em ${url}${hint}`);
  }
  return body as ClassificationResult;
}

async function classifyViaPython(text: string): Promise<ClassificationResult> {
  return new Promise((resolve, reject) => {
    const py = spawn(PYTHON, [CLASSIFY_SCRIPT], { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";

    py.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    py.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    py.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr || `classify.py exit ${code}`));
        return;
      }
      try {
        const parsed = JSON.parse(stdout.trim()) as ClassificationResult & { error?: string };
        if (parsed.error) reject(new Error(parsed.error));
        else resolve(parsed);
      } catch {
        reject(new Error(`Resposta invalida do classificador: ${stdout}`));
      }
    });

    py.stdin.write(JSON.stringify({ text }));
    py.stdin.end();
  });
}

export async function classifyText(text: string): Promise<ClassificationResult> {
  if (CLASSIFIER_API_BASE) {
    return classifyViaApi(text);
  }
  return classifyViaPython(text);
}
