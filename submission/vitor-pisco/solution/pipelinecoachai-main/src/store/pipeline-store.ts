import { create } from 'zustand';
import type { PipelineDeal, SalesTeam, Product, Account, Metadata, FileUploadState, ActionRecord } from '@/types/csv';

interface PipelineStore {
  // CSV data
  pipeline: PipelineDeal[];
  teams: SalesTeam[];
  products: Product[];
  accounts: Account[];
  metadata: Metadata[];

  // Upload state
  fileStates: Record<string, FileUploadState>;

  // Session state
  selectedAgent: string;
  selectedManager: string;
  actions: ActionRecord[];
  dismissedDeals: string[];

  // Actions
  setPipeline: (data: PipelineDeal[]) => void;
  setTeams: (data: SalesTeam[]) => void;
  setProducts: (data: Product[]) => void;
  setAccounts: (data: Account[]) => void;
  setMetadata: (data: Metadata[]) => void;
  setFileState: (filename: string, state: FileUploadState) => void;
  setSelectedAgent: (agent: string) => void;
  setSelectedManager: (manager: string) => void;
  addAction: (action: ActionRecord) => void;
  dismissDeal: (dealId: string) => void;
  isDataLoaded: () => boolean;
}

export const usePipelineStore = create<PipelineStore>((set, get) => ({
  pipeline: [],
  teams: [],
  products: [],
  accounts: [],
  metadata: [],
  fileStates: {
    'sales_pipeline.csv': { status: 'waiting', rowCount: 0 },
    'sales_teams.csv': { status: 'waiting', rowCount: 0 },
    'products.csv': { status: 'waiting', rowCount: 0 },
    'accounts.csv': { status: 'waiting', rowCount: 0 },
    'metadata.csv': { status: 'waiting', rowCount: 0 },
  },
  selectedAgent: '',
  selectedManager: '',
  actions: [],
  dismissedDeals: [],

  setPipeline: (data) => set({ pipeline: data }),
  setTeams: (data) => set({ teams: data }),
  setProducts: (data) => set({ products: data }),
  setAccounts: (data) => set({ accounts: data }),
  setMetadata: (data) => set({ metadata: data }),
  setFileState: (filename, state) =>
    set((s) => ({ fileStates: { ...s.fileStates, [filename]: state } })),
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  setSelectedManager: (manager) => set({ selectedManager: manager }),
  addAction: (action) => set((s) => ({ actions: [...s.actions, action] })),
  dismissDeal: (dealId) => set((s) => ({ dismissedDeals: [...s.dismissedDeals, dealId] })),
  isDataLoaded: () => get().fileStates['sales_pipeline.csv']?.status === 'loaded',
}));
