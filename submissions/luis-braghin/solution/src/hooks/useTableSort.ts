import { useState, useMemo, useCallback } from "react";

export type SortDirection = "asc" | "desc";

export interface SortConfig<T extends string = string> {
  key: T;
  direction: SortDirection;
}

export function useTableSort<T extends string = string>(defaultKey: T, defaultDirection: SortDirection = "desc") {
  const [sortConfig, setSortConfig] = useState<SortConfig<T>>({ key: defaultKey, direction: defaultDirection });

  const toggleSort = useCallback((key: T) => {
    setSortConfig(prev =>
      prev.key === key
        ? { key, direction: prev.direction === "desc" ? "asc" : "desc" }
        : { key, direction: "desc" }
    );
  }, []);

  return { sortConfig, toggleSort };
}

export function sortData<T>(data: T[], key: string, direction: SortDirection): T[] {
  return [...data].sort((a, b) => {
    const aVal = (a as Record<string, unknown>)[key];
    const bVal = (b as Record<string, unknown>)[key];

    if (aVal == null && bVal == null) return 0;
    if (aVal == null) return 1;
    if (bVal == null) return -1;

    let cmp = 0;
    if (typeof aVal === "number" && typeof bVal === "number") {
      cmp = aVal - bVal;
    } else {
      cmp = String(aVal).localeCompare(String(bVal));
    }

    return direction === "asc" ? cmp : -cmp;
  });
}
