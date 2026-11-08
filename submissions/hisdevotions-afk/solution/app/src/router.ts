import { useEffect, useSyncExternalStore } from "react";

// Rotas em hash (#/deal/ID): funcionam no GitHub Pages sem configurar fallback de 404.

const subscribe = (cb: () => void) => {
  window.addEventListener("hashchange", cb);
  return () => window.removeEventListener("hashchange", cb);
};

export function useRoute() {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash);
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [hash.split("?")[0]]);
  const [path, query = ""] = hash.replace(/^#\/?/, "").split("?");
  return {
    parts: path.split("/").filter(Boolean).map(decodeURIComponent),
    query: new URLSearchParams(query),
  };
}

export const link = (...parts: string[]) => "#/" + parts.map(encodeURIComponent).join("/");
