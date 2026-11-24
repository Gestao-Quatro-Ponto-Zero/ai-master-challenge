import { useEffect, useState } from "react";

export type Theme = "light" | "dark" | "auto";
const VARS = ["--s1", "--s2", "--s3", "--neutral", "--ink", "--ink-2", "--muted", "--grid", "--axis", "--surface", "--critical"] as const;
export type Palette = Record<(typeof VARS)[number], string>;

function read(): Palette {
  const cs = getComputedStyle(document.documentElement);
  return Object.fromEntries(VARS.map((v) => [v, cs.getPropertyValue(v).trim()])) as Palette;
}

function load(): Theme {
  try {
    const t = localStorage.getItem("theme");
    return t === "light" || t === "dark" ? t : "auto";
  } catch {
    return "auto";
  }
}

/** Tema escolhido + cores resolvidas (o Recharts precisa de cor literal, não de var()). */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(load);
  const [pal, setPal] = useState<Palette>(read);

  useEffect(() => {
    const el = document.documentElement;
    if (theme === "auto") delete el.dataset.theme;
    else el.dataset.theme = theme;
    try {
      if (theme === "auto") localStorage.removeItem("theme");
      else localStorage.setItem("theme", theme);
    } catch {
      /* armazenamento indisponível: segue só na sessão */
    }
    setPal(read());
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const on = () => setPal(read());
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [theme]);

  const isDark = theme === "dark" || (theme === "auto" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const toggle = () => setTheme(isDark ? "light" : "dark");
  return { pal, isDark, toggle };
}
