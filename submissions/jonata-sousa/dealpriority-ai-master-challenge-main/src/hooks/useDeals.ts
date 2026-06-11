import { useState, useEffect, useMemo } from "react";
import { supabase } from "@/integrations/supabase/client";
import type { Deal } from "@/types/deal";

export interface Filters {
  search: string;
  sales_agent: string;
  manager: string;
  regional_office: string;
  product: string;
  deal_stage: string;
  priority_label: string;
}

const emptyFilters: Filters = {
  search: "",
  sales_agent: "",
  manager: "",
  regional_office: "",
  product: "",
  deal_stage: "",
  priority_label: "",
};

export function useDeals() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [sortAsc, setSortAsc] = useState(false);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  useEffect(() => {
    async function fetchDeals() {
      // Fetch all deals (paginate if > 1000)
      let allRows: Deal[] = [];
      let from = 0;
      const batchSize = 1000;
      let hasMore = true;

      while (hasMore) {
        const { data, error } = await supabase
          .from("deals")
          .select("*")
          .range(from, from + batchSize - 1);

        if (error) {
          console.error("Error fetching deals:", error);
          break;
        }

        if (data) {
          allRows = [...allRows, ...(data as unknown as Deal[])];
          hasMore = data.length === batchSize;
          from += batchSize;
        } else {
          hasMore = false;
        }
      }

      setDeals(allRows);
      setLoading(false);
    }

    fetchDeals();
  }, []);

  const filterOptions = useMemo(() => {
    const unique = (key: keyof Deal) =>
      [...new Set(deals.map((d) => d[key] as string).filter(Boolean))].sort();
    return {
      sales_agent: unique("sales_agent"),
      manager: unique("manager"),
      regional_office: unique("regional_office"),
      product: unique("product"),
      deal_stage: unique("deal_stage"),
      priority_label: unique("priority_label"),
    };
  }, [deals]);

  // Reset to page 1 when filters or sort change
  useEffect(() => {
    setPage(1);
  }, [filters, sortAsc]);

  const filtered = useMemo(() => {
    let result = deals;

    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (d) =>
          d.account?.toLowerCase().includes(q) ||
          d.opportunity_id?.toLowerCase().includes(q) ||
          d.sales_agent?.toLowerCase().includes(q)
      );
    }

    const keys: (keyof Filters)[] = [
      "sales_agent",
      "manager",
      "regional_office",
      "product",
      "deal_stage",
      "priority_label",
    ];
    for (const k of keys) {
      if (filters[k]) {
        result = result.filter((d) => d[k as keyof Deal] === filters[k]);
      }
    }

    result = [...result].sort((a, b) =>
      sortAsc
        ? a.priority_score - b.priority_score
        : b.priority_score - a.priority_score
    );

    return result;
  }, [deals, filters, sortAsc]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, totalPages);
  const paginatedDeals = filtered.slice((safePage - 1) * pageSize, safePage * pageSize);

  return {
    deals: paginatedDeals,
    filteredDeals: filtered,
    allDeals: deals,
    totalFiltered: filtered.length,
    filters,
    setFilters,
    sortAsc,
    setSortAsc,
    filterOptions,
    loading,
    resetFilters: () => setFilters(emptyFilters),
    page: safePage,
    setPage,
    pageSize,
    setPageSize: (size: number) => { setPageSize(size); setPage(1); },
    totalPages,
  };
}
