"use client";

import { useEffect, useState } from "react";
import { type ScoredDeal } from "@/lib/scoring";
import { ManagerView } from "../components/ManagerView";
import { Navbar } from "../components/Navbar";

export default function ManagerPage() {
  const [activeDeals, setActiveDeals] = useState<ScoredDeal[]>([]);
  const [allDeals, setAllDeals] = useState<ScoredDeal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("/api/deals",     { cache: "no-store" }).then((r) => r.json()),
      fetch("/api/all-deals", { cache: "no-store" }).then((r) => r.json()),
    ])
      .then(([active, all]) => {
        setActiveDeals(active);
        setAllDeals(all);
        setLoading(false);
      })
      .catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Navbar />

      <main className="max-w-screen-2xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white">Painel do Time</h2>
          <p className="text-gray-500 text-sm mt-1">
            Performance e deals em risco por vendedor
          </p>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 mt-4">Carregando dados do time...</p>
          </div>
        ) : (
          <ManagerView deals={activeDeals} allDeals={allDeals} />
        )}
      </main>
    </div>
  );
}
