"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { cn } from "@/lib/utils";
import { ScenarioBadge } from "@/components/prototype/scenario-badge";
import {
  Filter,
  MessageSquare,
  Clock,
  User,
  RefreshCw,
  Bot,
  Headset,
  Search,
  Timer,
  UserPlus,
  ArrowRightLeft,
  X,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

// ─── Types ───────────────────────────────────────────────────────────

export interface ConversationSummary {
  id: string;
  customer_name: string | null;
  customer_email: string | null;
  channel: string;
  status: string;
  category_classified: string | null;
  subject_classified: string | null;
  scenario: string | null;
  turn_count: number;
  created_at: string;
  updated_at: string;
  sla_deadline: string | null;
  escalation_tier: number | null;
  assigned_operator_id: string | null;
}

interface Operator {
  id: string;
  name: string;
  level: string;
}

interface ConversationQueueProps {
  selectedId: string | null;
  onSelect: (conv: ConversationSummary) => void;
  onAccept?: (conversationId: string) => Promise<void>;
  operators?: Array<{ id: string; name: string; status: string; active_tickets: number; max_capacity: number }>;
  currentOperatorId?: string | null;
  onTransfer?: (conversationId: string, toOperatorId: string) => Promise<void>;
}

// ─── Filter Options ──────────────────────────────────────────────────

const CATEGORY_OPTIONS = [
  { value: "all", label: "Todas categorias" },
  { value: "Access", label: "Access" },
  { value: "Administrative rights", label: "Admin Rights" },
  { value: "Hardware", label: "Hardware" },
  { value: "HR Support", label: "HR Support" },
  { value: "Internal Project", label: "Internal Project" },
  { value: "Miscellaneous", label: "Miscellaneous" },
  { value: "Purchase", label: "Purchase" },
  { value: "Storage", label: "Storage" },
];

const SCENARIO_OPTIONS = [
  { value: "all", label: "Todos cenarios" },
  { value: "acelerar", label: "Acelerar" },
  { value: "desacelerar", label: "Desacelerar" },
  { value: "redirecionar", label: "Redirecionar" },
  { value: "quarentena", label: "Quarentena" },
  { value: "manter", label: "Manter" },
  { value: "liberar", label: "Liberar" },
];

// ─── Kanban Column Definitions ──────────────────────────────────────

interface KanbanColumn {
  key: string;
  label: string;
  headerColor: string;
  bgColor: string;
  filter: (conv: ConversationSummary) => boolean;
}

const KANBAN_COLUMNS: KanbanColumn[] = [
  {
    key: "novos",
    label: "Novos",
    headerColor: "bg-green-600 text-white",
    bgColor: "bg-green-50/50 dark:bg-green-950/20",
    filter: (c) => c.status === "active" && !c.category_classified,
  },
  {
    key: "ia_processando",
    label: "IA Processando",
    headerColor: "bg-violet-600 text-white",
    bgColor: "bg-violet-50/50 dark:bg-violet-950/20",
    filter: (c) => c.status === "active" && !!c.category_classified && !c.assigned_operator_id,
  },
  {
    key: "escalados",
    label: "Escalados",
    headerColor: "bg-orange-500 text-white",
    bgColor: "bg-orange-50/50 dark:bg-orange-950/20",
    filter: (c) => c.status === "escalated",
  },
  {
    key: "em_atendimento",
    label: "Em Atendimento",
    headerColor: "bg-blue-600 text-white",
    bgColor: "bg-blue-50/50 dark:bg-blue-950/20",
    filter: (c) => c.status === "in_progress",
  },
  {
    key: "resolvidos",
    label: "Resolvidos",
    headerColor: "bg-gray-500 text-white",
    bgColor: "bg-gray-50/50 dark:bg-gray-950/20",
    filter: (c) => c.status === "resolved",
  },
  {
    key: "fechados",
    label: "Fechados",
    headerColor: "bg-gray-700 text-white",
    bgColor: "bg-gray-100/50 dark:bg-gray-900/30",
    filter: (c) => {
      if (c.status === "closed" || c.status === "idle") return true;
      // Active conversations idle for > 15 minutes
      if (c.status === "active" && c.assigned_operator_id && c.category_classified) {
        const updatedAt = new Date(c.updated_at).getTime();
        const fifteenMinAgo = Date.now() - 15 * 60 * 1000;
        return updatedAt < fifteenMinAgo;
      }
      return false;
    },
  },
];

// ─── SLA Helpers ────────────────────────────────────────────────────

function getSlaInfo(slaDeadline: string | null): {
  label: string;
  color: "green" | "yellow" | "red" | "expired";
  minutesLeft: number;
} | null {
  if (!slaDeadline) return null;
  const ms = new Date(slaDeadline).getTime() - Date.now();
  const minutes = Math.floor(ms / 60000);

  if (ms <= 0) {
    return { label: "SLA EXPIRADO", color: "expired", minutesLeft: minutes };
  }
  if (minutes < 10) {
    return { label: `SLA EM RISCO`, color: "red", minutesLeft: minutes };
  }
  if (minutes < 30) {
    return { label: `${minutes}min`, color: "yellow", minutesLeft: minutes };
  }
  return { label: "SLA OK", color: "green", minutesLeft: minutes };
}

function SlaIndicator({ slaDeadline }: { slaDeadline: string }) {
  const [info, setInfo] = useState(() => getSlaInfo(slaDeadline));

  useEffect(() => {
    const update = () => setInfo(getSlaInfo(slaDeadline));
    update();
    const interval = setInterval(update, 10000);
    return () => clearInterval(interval);
  }, [slaDeadline]);

  if (!info) return null;

  const dotClasses = {
    green: "bg-green-500",
    yellow: "bg-yellow-500",
    red: "bg-red-500 animate-pulse",
    expired: "bg-red-600 animate-pulse",
  };

  const textClasses = {
    green: "text-green-700",
    yellow: "text-yellow-600",
    red: "text-red-600 font-semibold",
    expired: "text-red-700 font-bold",
  };

  return (
    <span className={cn("flex items-center gap-1 text-[10px] font-medium", textClasses[info.color])}>
      <span className={cn("inline-block h-1.5 w-1.5 rounded-full", dotClasses[info.color])} />
      {info.label}
    </span>
  );
}

// ─── Channel Icon ──────────────────────────────────────────────────

function ChannelIcon({ channel }: { channel: string }) {
  const ch = channel?.toLowerCase();
  if (ch === "email") return <MessageSquare className="h-2.5 w-2.5" />;
  if (ch === "phone" || ch === "telefone") return <MessageSquare className="h-2.5 w-2.5" />;
  if (ch === "chat") return <MessageSquare className="h-2.5 w-2.5" />;
  return <MessageSquare className="h-2.5 w-2.5" />;
}

// ─── Kanban Card ────────────────────────────────────────────────────

function KanbanCard({
  conv,
  isSelected,
  onSelect,
  operatorMap,
  onAccept,
  operators,
  onTransfer,
}: {
  conv: ConversationSummary;
  isSelected: boolean;
  onSelect: (conv: ConversationSummary) => void;
  operatorMap: Record<string, string>;
  onAccept?: (conversationId: string) => Promise<void>;
  operators?: Array<{ id: string; name: string; status: string; active_tickets: number; max_capacity: number }>;
  onTransfer?: (conversationId: string, toOperatorId: string) => Promise<void>;
}) {
  const [showActions, setShowActions] = useState(false);
  const [showTransferMenu, setShowTransferMenu] = useState(false);
  const slaInfo = getSlaInfo(conv.sla_deadline);
  const isUnassigned = !conv.assigned_operator_id;
  const operatorName = conv.assigned_operator_id
    ? operatorMap[conv.assigned_operator_id] || "Operador"
    : null;

  // SLA-based border and background
  let slaBorderClass = "";
  let slaBgClass = "";
  if (slaInfo) {
    if (slaInfo.color === "expired") {
      slaBorderClass = "border-l-4 border-l-red-500";
      slaBgClass = "bg-red-50/60";
    } else if (slaInfo.color === "red") {
      slaBorderClass = "border-l-4 border-l-red-400";
      slaBgClass = "bg-red-50/30";
    } else if (slaInfo.color === "yellow") {
      slaBorderClass = "border-l-4 border-l-yellow-400";
    }
  }

  return (
    <div
      className="relative"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false);
        setShowTransferMenu(false);
      }}
    >
      <button
        onClick={() => onSelect(conv)}
        className={cn(
          "w-full rounded-lg border bg-white p-2.5 text-left transition-all shadow-sm hover:shadow-md",
          isSelected
            ? "ring-2 ring-primary border-primary"
            : "hover:border-gray-300",
          slaBorderClass,
          slaBgClass
        )}
      >
        {/* Row 1: Name + SLA */}
        <div className="flex items-center justify-between gap-1">
          <div className="flex items-center gap-1 min-w-0">
            <User className="h-3 w-3 shrink-0 text-muted-foreground" />
            <span className="text-xs font-medium truncate">
              {conv.customer_name || "Anonimo"}
            </span>
          </div>
          {conv.sla_deadline && <SlaIndicator slaDeadline={conv.sla_deadline} />}
        </div>

        {/* Row 2: Category + subject badges */}
        <div className="mt-1.5 flex items-center gap-1 flex-wrap">
          {conv.category_classified && (
            <span className="rounded bg-violet-100 text-violet-800 px-1.5 py-0.5 text-[9px] font-semibold">
              {conv.category_classified}
            </span>
          )}
          {conv.subject_classified && (
            <span className="rounded bg-blue-100 text-blue-800 px-1.5 py-0.5 text-[9px] font-medium truncate max-w-[120px]">
              {conv.subject_classified}
            </span>
          )}
        </div>

        {/* Row 3: Channel + time + operator/IA + scenario */}
        <div className="mt-1.5 flex items-center justify-between gap-1">
          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-0.5">
              <ChannelIcon channel={conv.channel} />
              {conv.channel}
            </span>
            <span className="flex items-center gap-0.5">
              <Clock className="h-2.5 w-2.5" />
              {new Date(conv.created_at).toLocaleTimeString("pt-BR", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            {operatorName ? (
              <span className="flex items-center gap-0.5 text-blue-600">
                <Headset className="h-2.5 w-2.5" />
                <span className="truncate max-w-[60px]">{operatorName}</span>
              </span>
            ) : (
              <span className="flex items-center gap-0.5 text-violet-600">
                <Bot className="h-2.5 w-2.5" />
                IA
              </span>
            )}
          </div>
          {conv.scenario && (
            <ScenarioBadge scenario={conv.scenario} className="text-[8px] px-1 py-0" />
          )}
        </div>
      </button>

      {/* Hover action buttons overlay */}
      {showActions && (onAccept || onTransfer) && (
        <div className="absolute top-1 right-1 z-20 flex gap-1">
          {isUnassigned && onAccept && (
            <Button
              size="sm"
              className="h-6 px-2 text-[10px] bg-green-600 hover:bg-green-700 text-white"
              onClick={(e) => {
                e.stopPropagation();
                onAccept(conv.id);
              }}
            >
              <UserPlus className="h-3 w-3 mr-0.5" />
              Aceitar
            </Button>
          )}
          {!isUnassigned && onTransfer && (
            <div className="relative">
              <Button
                size="sm"
                variant="outline"
                className="h-6 px-2 text-[10px]"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowTransferMenu(!showTransferMenu);
                }}
              >
                <ArrowRightLeft className="h-3 w-3 mr-0.5" />
                Transferir
              </Button>
              {showTransferMenu && operators && (
                <div className="absolute top-7 right-0 z-30 w-40 rounded-lg border bg-white shadow-lg py-1">
                  {operators
                    .filter((op) => op.id !== conv.assigned_operator_id && op.status === "available" && op.active_tickets < op.max_capacity)
                    .map((op) => (
                      <button
                        key={op.id}
                        className="w-full px-3 py-1.5 text-left text-xs hover:bg-muted flex justify-between"
                        onClick={(e) => {
                          e.stopPropagation();
                          onTransfer(conv.id, op.id);
                          setShowTransferMenu(false);
                        }}
                      >
                        <span>{op.name}</span>
                        <span className="text-muted-foreground">{op.active_tickets}/{op.max_capacity}</span>
                      </button>
                    ))}
                  {operators.filter((op) => op.id !== conv.assigned_operator_id && op.status === "available" && op.active_tickets < op.max_capacity).length === 0 && (
                    <p className="px-3 py-1.5 text-xs text-muted-foreground">Nenhum disponivel</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────

export function ConversationQueue({
  selectedId,
  onSelect,
  onAccept,
  operators: externalOperators,
  currentOperatorId,
  onTransfer,
}: ConversationQueueProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [internalOperators, setInternalOperators] = useState<Operator[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [scenarioFilter, setScenarioFilter] = useState("all");
  const [operatorFilter, setOperatorFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Build operator lookup map
  const operatorMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const op of internalOperators) {
      map[op.id] = op.name;
    }
    if (externalOperators) {
      for (const op of externalOperators) {
        map[op.id] = op.name;
      }
    }
    return map;
  }, [internalOperators, externalOperators]);

  // Fetch operators once on mount
  useEffect(() => {
    async function fetchOperators() {
      try {
        const res = await fetch("/api/prototype/operators");
        if (res.ok) {
          const data = await res.json();
          setInternalOperators(data.operators || []);
        }
      } catch (err) {
        console.error("Erro ao buscar operadores:", err);
      }
    }
    fetchOperators();
  }, []);

  const fetchConversations = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (categoryFilter !== "all") params.set("category", categoryFilter);
      if (scenarioFilter !== "all") params.set("scenario", scenarioFilter);
      if (operatorFilter !== "all") params.set("operator", operatorFilter);
      params.set("limit", "50");

      const res = await fetch(`/api/prototype/conversations?${params}`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (err) {
      console.error("Erro ao buscar conversas:", err);
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, categoryFilter, scenarioFilter, operatorFilter]);

  // Fetch on mount and when filters change
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Auto-refresh every 5s
  useEffect(() => {
    const interval = setInterval(fetchConversations, 5000);
    return () => clearInterval(interval);
  }, [fetchConversations]);

  // Build operator filter options dynamically
  const operatorOptions = useMemo(() => {
    const ops = internalOperators.length > 0 ? internalOperators : (externalOperators || []);
    const opts = [
      { value: "all", label: "Todos operadores" },
      { value: "ia", label: "IA (sem operador)" },
    ];
    for (const op of ops) {
      opts.push({ value: op.id, label: op.name });
    }
    return opts;
  }, [internalOperators, externalOperators]);

  // Client-side search filter
  const searchFiltered = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter((c) => {
      return (
        (c.customer_name && c.customer_name.toLowerCase().includes(q)) ||
        (c.customer_email && c.customer_email.toLowerCase().includes(q)) ||
        (c.category_classified && c.category_classified.toLowerCase().includes(q)) ||
        (c.subject_classified && c.subject_classified.toLowerCase().includes(q))
      );
    });
  }, [conversations, searchQuery]);

  // Group conversations into Kanban columns
  // A conversation can only belong to the first matching column (avoid duplicates)
  const columns = useMemo(() => {
    const assigned = new Set<string>();
    return KANBAN_COLUMNS.map((col) => {
      const items = searchFiltered.filter((c) => {
        if (assigned.has(c.id)) return false;
        if (col.filter(c)) {
          assigned.add(c.id);
          return true;
        }
        return false;
      });
      return { ...col, items };
    });
  }, [searchFiltered]);

  // Status filter options for Kanban
  const STATUS_OPTIONS = [
    { value: "all", label: "Todos" },
    { value: "active", label: "Ativo" },
    { value: "escalated", label: "Escalado" },
    { value: "in_progress", label: "Em atendimento" },
    { value: "resolved", label: "Resolvido" },
  ];

  const activeFilters = [statusFilter, categoryFilter, scenarioFilter, operatorFilter].filter((f) => f !== "all").length;

  return (
    <div className="flex h-full flex-col">
      {/* Top bar: Search + Filters */}
      <div className="flex-none border-b bg-muted/20 px-3 py-2 space-y-2">
        {/* Search + filter toggle row */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Buscar por nome, email, categoria..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 pl-7 text-xs"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "relative rounded-md p-1.5 transition-colors",
              showFilters ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted"
            )}
          >
            <Filter className="h-4 w-4" />
            {activeFilters > 0 && (
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-primary text-[8px] font-bold text-white">
                {activeFilters}
              </span>
            )}
          </button>
          <button
            onClick={fetchConversations}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </button>
        </div>

        {/* Filter dropdowns row */}
        {showFilters && (
          <div className="flex flex-wrap gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-md border bg-background px-2 py-1 text-xs"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="rounded-md border bg-background px-2 py-1 text-xs"
            >
              {CATEGORY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <select
              value={scenarioFilter}
              onChange={(e) => setScenarioFilter(e.target.value)}
              className="rounded-md border bg-background px-2 py-1 text-xs"
            >
              {SCENARIO_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <select
              value={operatorFilter}
              onChange={(e) => setOperatorFilter(e.target.value)}
              className="rounded-md border bg-background px-2 py-1 text-xs"
            >
              {operatorOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Kanban board — horizontally scrollable */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-x-auto overflow-y-hidden"
      >
        <div className="flex h-full gap-3 p-3" style={{ minWidth: "fit-content" }}>
          {columns.map((col) => (
            <div
              key={col.key}
              className={cn(
                "flex h-full w-[220px] shrink-0 flex-col rounded-lg border",
                col.bgColor
              )}
            >
              {/* Column header */}
              <div className={cn("flex items-center justify-between rounded-t-lg px-3 py-2", col.headerColor)}>
                <span className="text-xs font-semibold">{col.label}</span>
                <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-white/20 px-1.5 text-[10px] font-bold">
                  {col.items.length}
                </span>
              </div>

              {/* Column cards */}
              <ScrollArea className="flex-1">
                <div className="space-y-2 p-2">
                  {col.items.length === 0 && (
                    <p className="py-4 text-center text-[10px] text-muted-foreground">
                      Nenhum ticket
                    </p>
                  )}
                  {col.items.map((conv) => (
                    <KanbanCard
                      key={conv.id}
                      conv={conv}
                      isSelected={selectedId === conv.id}
                      onSelect={onSelect}
                      operatorMap={operatorMap}
                      onAccept={onAccept}
                      operators={externalOperators}
                      onTransfer={onTransfer}
                    />
                  ))}
                </div>
              </ScrollArea>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
