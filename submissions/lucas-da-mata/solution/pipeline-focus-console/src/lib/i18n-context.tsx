import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  DEFAULT_LANG,
  LANG_STORAGE_KEY,
  fmtCompactUSD,
  fmtNumber,
  fmtUSD,
  priorityLabel,
  readSavedLang,
  stageLabel,
  translate,
  type Lang,
} from "./i18n";

interface I18nValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  num: (n: number) => string;
  usd: (n: number) => string;
  compactUsd: (n: number) => string;
  stage: (s: string) => string;
  priority: (p: string) => string;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(DEFAULT_LANG);

  // Always start in pt-BR; only override from a saved choice (never browser lang).
  useEffect(() => {
    setLangState(readSavedLang());
  }, []);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try {
      window.localStorage.setItem(LANG_STORAGE_KEY, l);
    } catch {
      // Non-critical persistence.
    }
  }, []);

  const value = useMemo<I18nValue>(
    () => ({
      lang,
      setLang,
      t: (key, params) => translate(lang, key, params),
      num: (n) => fmtNumber(n, lang),
      usd: (n) => fmtUSD(n, lang),
      compactUsd: (n) => fmtCompactUSD(n, lang),
      stage: (s) => stageLabel(s, lang),
      priority: (p) => priorityLabel(p, lang),
    }),
    [lang, setLang],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
