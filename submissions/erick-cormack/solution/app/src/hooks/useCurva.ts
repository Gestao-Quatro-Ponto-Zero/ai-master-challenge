import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";

export type PontoCurva = { idade: number; p_ganho: number; n_sobreviventes: number };

export function useCurva() {
  return useQuery({
    queryKey: ["curva-ganho"],
    staleTime: Infinity,
    queryFn: async (): Promise<PontoCurva[]> => {
      const { data, error } = await supabase
        .from("v_curva_ganho")
        .select("*")
        .order("idade");
      if (error) throw new Error(error.message);
      return (data ?? []).map((r) => ({
        idade: r.idade ?? 0,
        p_ganho: r.p_ganho ?? 0,
        n_sobreviventes: r.n_sobreviventes ?? 0,
      }));
    },
  });
}
