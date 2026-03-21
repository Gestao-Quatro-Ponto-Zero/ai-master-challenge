import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import type { Lead } from "@/lib/types";
import { parseWorkbookFromUrl, parseWorkbookBuffer } from "@/lib/parseWorkbook";
import { computeScores } from "@/lib/scoring";
import { parseSector, parseEmployees, getEmployeeBucket, isInvalid } from "@/lib/dataHelpers";

interface DataContextType {
  leads: Lead[];
  loading: boolean;
  error: string | null;
  uploadFile: (file: File) => Promise<void>;
  updateLead: (opportunityId: string, updates: { sector?: string; employees?: number }) => void;
  managers: string[];
  salesAgents: string[];
}

const DataContext = createContext<DataContextType | null>(null);

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    parseWorkbookFromUrl("/data/seed.xlsx")
      .then(setLeads)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const buf = await file.arrayBuffer();
      setLeads(parseWorkbookBuffer(buf));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateLead = useCallback((opportunityId: string, updates: { sector?: string; employees?: number }) => {
    setLeads(prev => {
      const updated = prev.map(l => {
        if (l.opportunity_id !== opportunityId) return l;
        const newLead = { ...l };
        if (updates.sector !== undefined) {
          newLead.sector = updates.sector || null;
        }
        if (updates.employees !== undefined) {
          newLead.employees = updates.employees;
          newLead.employeeBucket = getEmployeeBucket(updates.employees);
        }
        // Recalculate incomplete status
        const missing: string[] = [];
        if (!newLead.sector) missing.push("setor");
        if (newLead.employees === null) missing.push("porte");
        newLead.isIncomplete = missing.length > 0;
        newLead.missingFields = missing;
        return newLead;
      });
      // Recalculate all scores since quartiles depend on the full dataset
      return computeScores(updated);
    });
  }, []);

  const managers = React.useMemo(() => [...new Set(leads.map(l => l.manager).filter(Boolean))].sort(), [leads]);
  const salesAgents = React.useMemo(() => [...new Set(leads.map(l => l.sales_agent).filter(Boolean))].sort(), [leads]);

  return (
    <DataContext.Provider value={{ leads, loading, error, uploadFile, updateLead, managers, salesAgents }}>
      {children}
    </DataContext.Provider>
  );
}

export function useData() {
  const ctx = useContext(DataContext);
  if (!ctx) throw new Error("useData must be used within DataProvider");
  return ctx;
}
