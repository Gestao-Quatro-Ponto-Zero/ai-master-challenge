import { useQuery } from "@tanstack/react-query";
import type { G4Data, ScoredDeal, ClosedDeal, Agent, Product, Account, Analytics, TeamStructure } from "@/types/deals";
import rawData from "@/data/g4-deal-intelligence-data.json";

const data = rawData as unknown as G4Data;

export function useDeals() {
  return useQuery<ScoredDeal[]>({
    queryKey: ["deals"],
    queryFn: () => data.scoredDeals,
    staleTime: Infinity,
  });
}

export function useClosedDeals() {
  return useQuery<ClosedDeal[]>({
    queryKey: ["closedDeals"],
    queryFn: () => data.closedDeals,
    staleTime: Infinity,
  });
}

export function useAgents() {
  return useQuery<Agent[]>({
    queryKey: ["agents"],
    queryFn: () => data.agents,
    staleTime: Infinity,
  });
}

export function useProducts() {
  return useQuery<Product[]>({
    queryKey: ["products"],
    queryFn: () => data.products,
    staleTime: Infinity,
  });
}

export function useAccounts() {
  return useQuery<Account[]>({
    queryKey: ["accounts"],
    queryFn: () => data.accounts,
    staleTime: Infinity,
  });
}

export function useAnalytics() {
  return useQuery<Analytics>({
    queryKey: ["analytics"],
    queryFn: () => data.analytics,
    staleTime: Infinity,
  });
}

export function useTeamStructure() {
  return useQuery<TeamStructure>({
    queryKey: ["teamStructure"],
    queryFn: () => data.teamStructure,
    staleTime: Infinity,
  });
}

export function useEnrichment(accountName: string) {
  return useQuery({
    queryKey: ["enrichment", accountName],
    queryFn: () => data.enrichment[accountName] ?? null,
    staleTime: Infinity,
  });
}

export function useReferenceDate() {
  return data.referenceDate;
}
