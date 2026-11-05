export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.18"
  }
  public: {
    Tables: {
      accounts: {
        Row: {
          account: string
          employees: number | null
          office_location: string | null
          revenue: number | null
          sector: string | null
          subsidiary_of: string | null
          year_established: number | null
        }
        Insert: {
          account: string
          employees?: number | null
          office_location?: string | null
          revenue?: number | null
          sector?: string | null
          subsidiary_of?: string | null
          year_established?: number | null
        }
        Update: {
          account?: string
          employees?: number | null
          office_location?: string | null
          revenue?: number | null
          sector?: string | null
          subsidiary_of?: string | null
          year_established?: number | null
        }
        Relationships: []
      }
      parametros: {
        Row: {
          amostra_minima: number
          ciclo_max_dias: number
          data_referencia: string
          fase_risco_dias: number
          id: number
          reta_final_dias: number
        }
        Insert: {
          amostra_minima?: number
          ciclo_max_dias: number
          data_referencia: string
          fase_risco_dias: number
          id?: number
          reta_final_dias: number
        }
        Update: {
          amostra_minima?: number
          ciclo_max_dias?: number
          data_referencia?: string
          fase_risco_dias?: number
          id?: number
          reta_final_dias?: number
        }
        Relationships: []
      }
      products: {
        Row: {
          product: string
          sales_price: number
          series: string
        }
        Insert: {
          product: string
          sales_price: number
          series: string
        }
        Update: {
          product?: string
          sales_price?: number
          series?: string
        }
        Relationships: []
      }
      sales_pipeline: {
        Row: {
          account: string | null
          close_date: string | null
          close_value: number | null
          deal_stage: string
          engage_date: string | null
          opportunity_id: string
          product: string
          sales_agent: string
        }
        Insert: {
          account?: string | null
          close_date?: string | null
          close_value?: number | null
          deal_stage: string
          engage_date?: string | null
          opportunity_id: string
          product: string
          sales_agent: string
        }
        Update: {
          account?: string | null
          close_date?: string | null
          close_value?: number | null
          deal_stage?: string
          engage_date?: string | null
          opportunity_id?: string
          product?: string
          sales_agent?: string
        }
        Relationships: [
          {
            foreignKeyName: "sales_pipeline_account_fkey"
            columns: ["account"]
            isOneToOne: false
            referencedRelation: "accounts"
            referencedColumns: ["account"]
          },
          {
            foreignKeyName: "sales_pipeline_product_fkey"
            columns: ["product"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["product"]
          },
          {
            foreignKeyName: "sales_pipeline_sales_agent_fkey"
            columns: ["sales_agent"]
            isOneToOne: false
            referencedRelation: "sales_teams"
            referencedColumns: ["sales_agent"]
          },
        ]
      }
      sales_teams: {
        Row: {
          manager: string
          regional_office: string
          sales_agent: string
        }
        Insert: {
          manager: string
          regional_office: string
          sales_agent: string
        }
        Update: {
          manager?: string
          regional_office?: string
          sales_agent?: string
        }
        Relationships: []
      }
    }
    Views: {
      v_curva_ganho: {
        Row: {
          idade: number | null
          n_sobreviventes: number | null
          p_ganho: number | null
        }
        Relationships: []
      }
      v_deals_score: {
        Row: {
          account: string | null
          close_date: string | null
          close_value: number | null
          deal_stage: string | null
          dias_ate_limite: number | null
          employees: number | null
          engage_date: string | null
          fila: string | null
          idade_dias: number | null
          manager: string | null
          momento: string | null
          motivos: string[] | null
          office_location: string | null
          opportunity_id: string | null
          p_ganho: number | null
          possivel_duplicata: boolean | null
          prazo_limite: string | null
          product: string | null
          regional_office: string | null
          revenue: number | null
          sales_agent: string | null
          sales_price: number | null
          score: number | null
          sector: string | null
          sem_conta: boolean | null
          series: string | null
          valor_esperado: number | null
        }
        Relationships: [
          {
            foreignKeyName: "sales_pipeline_account_fkey"
            columns: ["account"]
            isOneToOne: false
            referencedRelation: "accounts"
            referencedColumns: ["account"]
          },
          {
            foreignKeyName: "sales_pipeline_product_fkey"
            columns: ["product"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["product"]
          },
          {
            foreignKeyName: "sales_pipeline_sales_agent_fkey"
            columns: ["sales_agent"]
            isOneToOne: false
            referencedRelation: "sales_teams"
            referencedColumns: ["sales_agent"]
          },
        ]
      }
      v_resumo_vendedor: {
        Row: {
          deals_focar: number | null
          deals_possivel_duplicata: number | null
          deals_prospectar: number | null
          deals_requalificar: number | null
          deals_reta_final: number | null
          deals_sem_conta: number | null
          ganhos: number | null
          manager: string | null
          perdidos: number | null
          regional_office: string | null
          sales_agent: string | null
          valor_esperado_focar: number | null
          valor_parado: number | null
        }
        Relationships: [
          {
            foreignKeyName: "sales_pipeline_sales_agent_fkey"
            columns: ["sales_agent"]
            isOneToOne: false
            referencedRelation: "sales_teams"
            referencedColumns: ["sales_agent"]
          },
        ]
      }
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
