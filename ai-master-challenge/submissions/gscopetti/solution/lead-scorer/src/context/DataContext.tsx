import React, { createContext, useContext, useReducer, type ReactNode } from 'react';
import type {
  Account,
  Product,
  SalesTeam,
  PipelineOpportunity,
  DealScore,
  AccountScore,
  AppData,
} from '@/types';

interface DataContextType {
  state: AppData & { errors: string[]; isLoaded: boolean };
  dispatch: React.Dispatch<Action>;
}

type Action =
  | {
      type: 'LOAD_DATA';
      payload: {
        accounts: Account[];
        products: Product[];
        salesTeams: SalesTeam[];
        pipeline: PipelineOpportunity[];
      };
    }
  | {
      type: 'SET_SCORES';
      payload: {
        dealScores: DealScore[];
        accountScores: AccountScore[];
      };
    }
  | {
      type: 'ADD_ERROR';
      payload: string;
    }
  | {
      type: 'RESET_DATA';
    };

const initialState: AppData & { errors: string[]; isLoaded: boolean } = {
  accounts: [],
  products: [],
  salesTeams: [],
  pipeline: [],
  dealScores: [],
  accountScores: [],
  errors: [],
  isLoaded: false,
};

function dataReducer(
  state: typeof initialState,
  action: Action
): typeof initialState {
  switch (action.type) {
    case 'LOAD_DATA':
      return {
        ...state,
        accounts: action.payload.accounts,
        products: action.payload.products,
        salesTeams: action.payload.salesTeams,
        pipeline: action.payload.pipeline,
        errors: [],
        isLoaded: true,
      };

    case 'SET_SCORES':
      return {
        ...state,
        dealScores: action.payload.dealScores,
        accountScores: action.payload.accountScores,
      };

    case 'ADD_ERROR':
      return {
        ...state,
        errors: [...state.errors, action.payload],
      };

    case 'RESET_DATA':
      return initialState;

    default:
      return state;
  }
}

const DataContext = createContext<DataContextType | undefined>(undefined);

/**
 * Provider component for data context
 */
export function DataProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(dataReducer, initialState);

  return (
    <DataContext.Provider value={{ state, dispatch }}>
      {children}
    </DataContext.Provider>
  );
}

/**
 * Hook to use data context
 */
export function useDataContext() {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useDataContext must be used within DataProvider');
  }
  return context;
}

/**
 * Helper action creators
 */
export const dataActions = {
  loadData: (
    accounts: Account[],
    products: Product[],
    salesTeams: SalesTeam[],
    pipeline: PipelineOpportunity[]
  ) => ({
    type: 'LOAD_DATA' as const,
    payload: { accounts, products, salesTeams, pipeline },
  }),

  setScores: (dealScores: DealScore[], accountScores: AccountScore[]) => ({
    type: 'SET_SCORES' as const,
    payload: { dealScores, accountScores },
  }),

  addError: (error: string) => ({
    type: 'ADD_ERROR' as const,
    payload: error,
  }),

  resetData: () => ({
    type: 'RESET_DATA' as const,
  }),
};
