import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";
import type { Database } from "@/integrations/supabase/types";

export type ResumoVendedor = Database["public"]["Views"]["v_resumo_vendedor"]["Row"];

export function useResumoVendedores() {
  return useQuery({
    queryKey: ["resumo-vendedor"],
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error } = await supabase.from("v_resumo_vendedor").select("*");
      if (error) throw new Error(error.message);
      return data ?? [];
    },
  });
}
