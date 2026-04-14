import { useState } from "react";
import { useDeals } from "@/hooks/useDeals";
import { useAuth } from "@/hooks/useAuth";
import { KPICards } from "@/components/dashboard/KPICards";
import { ChartsSection } from "@/components/dashboard/ChartsSection";
import { FiltersBar } from "@/components/dashboard/FiltersBar";
import { DealsTable } from "@/components/dashboard/DealsTable";
import { DealDetail } from "@/components/dashboard/DealDetail";
import { Button } from "@/components/ui/button";
import type { Deal } from "@/types/deal";
import { Crosshair, LogOut } from "lucide-react";

export default function Index() {
  const { signOut } = useAuth();
  const {
    deals,
    allDeals,
    filteredDeals,
    totalFiltered,
    filters,
    setFilters,
    sortAsc,
    setSortAsc,
    filterOptions,
    loading,
    resetFilters,
    page,
    setPage,
    pageSize,
    setPageSize,
    totalPages,
  } = useDeals();

  const [selected, setSelected] = useState<Deal | null>(null);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-3">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-muted-foreground">Carregando pipeline...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header — Product branding */}
      <header className="bg-header text-header-foreground">
        <div className="container max-w-[1440px] mx-auto px-6 py-5 flex items-center gap-4">
          <div className="h-10 w-10 rounded-xl bg-primary/20 border border-primary/30 flex items-center justify-center">
            <Crosshair className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold tracking-tight leading-tight">
              DealPriority
            </h1>
            <p className="text-sm text-header-muted mt-0.5">
              Inteligência de priorização para operações comerciais
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-3 text-xs text-header-muted">
            <span className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-success animate-pulse" />
              {totalFiltered === allDeals.length
                ? `${allDeals.length} oportunidades ativas`
                : `${totalFiltered} de ${allDeals.length} oportunidades`}
            </span>
            <Button variant="ghost" size="sm" onClick={signOut} className="h-7 text-xs text-header-muted hover:text-header-foreground hover:bg-white/10">
              <LogOut className="h-3.5 w-3.5 mr-1" /> Sair
            </Button>
          </div>
        </div>
      </header>

      <main className="container max-w-[1440px] mx-auto px-6 py-6 space-y-5">
        <FiltersBar
          filters={filters}
          setFilters={setFilters}
          options={filterOptions}
          resetFilters={resetFilters}
        />
        <KPICards deals={filteredDeals} />
        <ChartsSection deals={filteredDeals} />
        <DealsTable
          deals={deals}
          sortAsc={sortAsc}
          onToggleSort={() => setSortAsc(!sortAsc)}
          onSelect={setSelected}
          selected={selected}
          page={page}
          totalPages={totalPages}
          totalFiltered={totalFiltered}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      </main>

      {/* Detail panel overlay */}
      {selected && (
        <>
          <div
            className="fixed inset-0 bg-foreground/30 backdrop-blur-sm z-40 transition-opacity"
            onClick={() => setSelected(null)}
          />
          <DealDetail deal={selected} onClose={() => setSelected(null)} />
        </>
      )}
    </div>
  );
}
