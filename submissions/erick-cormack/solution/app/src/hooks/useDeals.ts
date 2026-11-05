import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import type { Database } from "@/integrations/supabase/types";

export type Deal = Database["public"]["Views"]["v_deals_score"]["Row"];

const PAGE = 1000;

/** Todos os deals abertos (fila <> 'fechado'), paginando de 1.000 em 1.000. */
async function fetchOpenDeals(): Promise<Deal[]> {
  const all: Deal[] = [];
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await supabase
      .from("v_deals_score")
      .select("*")
      .neq("fila", "fechado")
      .order("opportunity_id")
      .range(from, from + PAGE - 1);
    if (error) throw new Error(error.message);
    all.push(...(data ?? []));
    if (!data || data.length < PAGE) break;
  }
  return all;
}

export function useDeals() {
  return useQuery({ queryKey: ["deals", "abertos"], queryFn: fetchOpenDeals, staleTime: Infinity });
}
