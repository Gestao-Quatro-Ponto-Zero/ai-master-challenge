import { useQuery } from "@tanstack/react-query";
import { supabase } from "@/integrations/supabase/client";

export function useParametros() {
  return useQuery({
    queryKey: ["parametros"],
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error } = await supabase.from("parametros").select("*").limit(1).single();
      if (error) throw new Error(error.message);
      return data;
    },
  });
}
