// Pre-classification gate + information density scoring
// Blocks low-information messages from reaching the classification pipeline

// ─── Types ───────────────────────────────────────────────────────────

export interface GateResult {
  passed: boolean;
  reason?: "greeting" | "too_short" | "gibberish" | "farewell" | "gratitude";
  suggestedResponse?: string;
}

export interface DensityResult {
  score: number; // 0.0 to 1.0
  tokenCount: number;
  technicalTerms: string[];
  problemVerbs: string[];
  hasErrorCode: boolean;
  hasProductName: boolean;
}

// ─── Constants ───────────────────────────────────────────────────────

const GREETING_PATTERNS = [
  /^(oi|olá|ola|hey|hi|hello|e\s*a[ií]|eai|eaí|fala)\b/i,
  /^(bom\s+dia|boa\s+tarde|boa\s+noite)\s*[!.,]?\s*$/i,
  /^(oi|olá|ola),?\s*(tudo\s+(bem|bom|certo|tranquilo)|como\s+vai)[?!.]?\s*$/i,
  /^(hey|hi|hello)\s*[!.,]?\s*$/i,
];

const FAREWELL_PATTERNS = [
  /^(tchau|até\s+mais|até\s+logo|adeus|bye|goodbye)\b/i,
  /^(valeu|vlw|falou|flw|tmj)\s*[!.]?\s*$/i,
];

const GRATITUDE_PATTERNS = [
  /^(obrigad[oa]|muito\s+obrigad[oa]|thanks|thank\s+you|agradecido|grato|grata)\b/i,
];

const STOPWORDS = new Set([
  "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
  "o", "a", "os", "as", "um", "uma", "uns", "umas",
  "que", "e", "é", "para", "com", "por", "se", "ao", "aos",
  "eu", "ele", "ela", "nós", "meu", "minha", "seu", "sua",
  "isso", "isto", "esse", "essa", "este", "esta",
  "mas", "ou", "nem", "já", "não", "sim",
  "me", "te", "lhe", "nos", "vos", "lhes",
  "muito", "bem", "aqui", "ali", "lá",
  "como", "quando", "onde",
  "oi", "olá", "bom", "boa",
]);

const TECHNICAL_TERMS = [
  "erro", "error", "tela", "sistema", "servidor", "server",
  "rede", "wifi", "wi-fi", "internet", "conexão", "conexao",
  "senha", "login", "acesso", "autenticação", "autenticacao",
  "atualização", "atualizacao", "update", "upgrade",
  "instalação", "instalacao", "instalar",
  "driver", "monitor", "impressora", "teclado", "mouse",
  "computador", "notebook", "laptop", "desktop", "pc",
  "windows", "linux", "mac", "macos",
  "email", "e-mail", "outlook", "teams",
  "vpn", "firewall", "proxy", "dns",
  "backup", "restore", "restaurar",
  "banco de dados", "database", "sql",
  "software", "hardware", "aplicativo", "app",
  "memória", "memoria", "ram", "hd", "ssd", "disco",
  "processador", "cpu", "placa",
  "navegador", "browser", "chrome", "firefox",
  "antivírus", "antivirus", "malware", "vírus", "virus",
  "permissão", "permissao", "admin", "administrador",
  "configuração", "configuracao", "config",
  "arquivo", "pasta", "diretório", "diretorio",
  "porta", "usb", "hdmi", "bluetooth",
  "conta", "perfil", "cadastro",
  "código", "codigo", "code",
  "api", "integração", "integracao",
  "lentidão", "lentidao", "lento", "travando",
  "tela azul", "blue screen", "bsod",
];

const PROBLEM_VERBS = [
  "travou", "parou", "não funciona", "nao funciona",
  "caiu", "lento", "crashou", "crasheou",
  "reinicia", "reiniciou", "desligou", "desliga",
  "sumiu", "apagou", "perdeu", "perdi",
  "bloqueou", "bloqueado", "bloqueada",
  "quebrou", "bugou", "bugado",
  "falhou", "falha", "falhando",
  "congelou", "congelando", "congela",
  "não abre", "nao abre", "não carrega", "nao carrega",
  "não conecta", "nao conecta", "não acessa", "nao acessa",
  "não entra", "nao entra", "não consigo", "nao consigo",
  "não aparece", "nao aparece", "não reconhece", "nao reconhece",
  "deu erro", "dando erro", "apareceu erro",
  "corrompeu", "corrompido", "corrompida",
  "esqueci", "esqueceu", "resetar", "redefinir",
];

const ERROR_CODE_PATTERNS = [
  /0x[0-9a-fA-F]{4,}/,
  /ERR[-_]\d+/i,
  /error\s+\d{3,}/i,
  /código\s+\d+/i,
  /codigo\s+\d+/i,
  /code\s+\d{3,}/i,
  /\b\d{3,4}\b.*erro/i,
  /erro.*\b\d{3,4}\b/i,
];

const PRODUCT_NAMES = [
  "dell", "hp", "lenovo", "asus", "acer", "samsung", "apple",
  "microsoft", "windows", "office", "excel", "word", "powerpoint",
  "outlook", "teams", "sharepoint", "onedrive",
  "google", "chrome", "gmail", "drive",
  "slack", "zoom", "jira", "confluence",
  "salesforce", "sap", "oracle", "totvs",
  "optiflow",
];

// ─── Portuguese Word Validation (simple heuristic) ──────────────────

const COMMON_PT_EN_WORDS = new Set([
  // Portuguese common words
  "ajuda", "preciso", "problema", "meu", "minha", "computador",
  "não", "nao", "funciona", "tela", "erro", "sistema", "rede",
  "qual", "status", "ticket", "quero", "tenho", "estou", "posso",
  "favor", "pode", "consegue", "urgente", "importante",
  "ontem", "hoje", "agora", "sempre", "nunca",
  // English common words
  "help", "need", "problem", "computer", "screen", "error",
  "system", "network", "want", "have", "please", "can",
  // Technical words (valid in both)
  "login", "email", "software", "hardware", "backup",
  "reset", "update", "install", "server", "wifi",
]);

function looksLikeRealWord(word: string): boolean {
  if (word.length < 2) return false;
  if (COMMON_PT_EN_WORDS.has(word)) return true;
  // Basic heuristic: has vowels and consonants, typical letter patterns
  const hasVowels = /[aeiouáéíóúãõâêîôû]/i.test(word);
  const hasConsonants = /[bcdfghjklmnpqrstvwxyz]/i.test(word);
  // Contains at least one vowel-consonant or consonant-vowel pair
  const hasNaturalPattern = /[aeiouáéíóúãõâêîôû][bcdfghjklmnpqrstvwxyz]|[bcdfghjklmnpqrstvwxyz][aeiouáéíóúãõâêîôû]/i.test(word);
  return hasVowels && hasConsonants && hasNaturalPattern;
}

// ─── Gate Check ─────────────────────────────────────────────────────

export function checkGate(message: string): GateResult {
  const trimmed = message.trim();

  // Empty or whitespace-only
  if (!trimmed) {
    return {
      passed: false,
      reason: "too_short",
      suggestedResponse: "Olá! Como posso ajudar você hoje? Descreva o problema que está enfrentando.",
    };
  }

  const lower = trimmed.toLowerCase();

  // Check greeting patterns
  for (const pattern of GREETING_PATTERNS) {
    if (pattern.test(lower)) {
      return {
        passed: false,
        reason: "greeting",
        suggestedResponse: "Olá! Bem-vindo ao suporte OptiFlow. Como posso ajudar você hoje?",
      };
    }
  }

  // Check farewell patterns
  for (const pattern of FAREWELL_PATTERNS) {
    if (pattern.test(lower)) {
      return {
        passed: false,
        reason: "farewell",
        suggestedResponse: "Até mais! Se precisar de algo, é só voltar. Tenha um ótimo dia!",
      };
    }
  }

  // Check gratitude patterns
  for (const pattern of GRATITUDE_PATTERNS) {
    if (pattern.test(lower)) {
      return {
        passed: false,
        reason: "gratitude",
        suggestedResponse: "De nada! Fico feliz em ajudar. Se tiver mais alguma dúvida, estou por aqui.",
      };
    }
  }

  // Extract meaningful words (remove stopwords)
  const words = lower
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .split(/\s+/)
    .filter((w) => w.length > 0);

  const meaningfulWords = words.filter((w) => !STOPWORDS.has(w) && w.length > 1);

  // Too short: less than 3 meaningful words
  if (meaningfulWords.length < 3) {
    return {
      passed: false,
      reason: "too_short",
      suggestedResponse: "Poderia descrever melhor o que está acontecendo? Quanto mais detalhes, mais rápido consigo ajudar.",
    };
  }

  // Gibberish detection: check if words look like real words
  const realWordCount = meaningfulWords.filter((w) => looksLikeRealWord(w)).length;
  const realWordRatio = realWordCount / meaningfulWords.length;

  if (realWordRatio < 0.4) {
    return {
      passed: false,
      reason: "gibberish",
      suggestedResponse: "Desculpe, não consegui entender sua mensagem. Poderia reformular descrevendo o problema que está enfrentando?",
    };
  }

  return { passed: true };
}

// ─── Information Density ────────────────────────────────────────────

export function computeDensity(message: string): DensityResult {
  const lower = message.toLowerCase();
  const words = lower
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .split(/\s+/)
    .filter((w) => w.length > 0);

  const tokenCount = words.length;

  // Find technical terms
  const foundTechnicalTerms: string[] = [];
  for (const term of TECHNICAL_TERMS) {
    if (lower.includes(term) && !foundTechnicalTerms.includes(term)) {
      foundTechnicalTerms.push(term);
    }
  }

  // Find problem verbs
  const foundProblemVerbs: string[] = [];
  for (const verb of PROBLEM_VERBS) {
    if (lower.includes(verb) && !foundProblemVerbs.includes(verb)) {
      foundProblemVerbs.push(verb);
    }
  }

  // Check for error codes
  const hasErrorCode = ERROR_CODE_PATTERNS.some((p) => p.test(message));

  // Check for product names
  const hasProductName = PRODUCT_NAMES.some((name) => lower.includes(name));

  // Calculate score
  const baseScore = Math.min(tokenCount / 15, 0.4);
  const techBonus = Math.min(foundTechnicalTerms.length * 0.15, 0.3);
  const verbBonus = Math.min(foundProblemVerbs.length * 0.1, 0.2);
  const errorCodeBonus = hasErrorCode ? 0.15 : 0;
  const productNameBonus = hasProductName ? 0.05 : 0;

  const rawScore = baseScore + techBonus + verbBonus + errorCodeBonus + productNameBonus;
  const score = Math.round(Math.min(Math.max(rawScore, 0), 1) * 100) / 100;

  return {
    score,
    tokenCount,
    technicalTerms: foundTechnicalTerms,
    problemVerbs: foundProblemVerbs,
    hasErrorCode,
    hasProductName,
  };
}

// ─── Effective Confidence ───────────────────────────────────────────

export function computeEffectiveConfidence(
  rawConfidence: number,
  densityScore: number
): number {
  return Math.round(rawConfidence * densityScore * 100) / 100;
}
