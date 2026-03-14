import { useState, useCallback } from 'react';
import Papa from 'papaparse';
import type {
  Account,
  Product,
  SalesTeam,
  PipelineOpportunity,
} from '@/types';
import {
  normalizeAccount,
  normalizeProduct,
  normalizeSalesTeamMember,
  normalizePipelineOpportunity,
  validateColumns,
} from '@/utils/normalizer';

const REQUIRED_COLUMNS = {
  accounts: ['account', 'sector', 'revenue', 'employees', 'office_location'],
  products: ['product', 'series', 'sales_price'],
  salesTeams: ['sales_agent', 'manager', 'regional_office'],
  pipeline: ['opportunity_id', 'sales_agent', 'product', 'deal_stage', 'engage_date', 'close_value'],
};

interface ParseResult {
  accounts: Account[];
  products: Product[];
  salesTeams: SalesTeam[];
  pipeline: PipelineOpportunity[];
  errors: string[];
}

/**
 * Hook to load and process CSV files
 */
export function useDataLoader() {
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  /**
   * Parse a CSV file using PapaParse
   */
  const parseCSV = useCallback(
    (file: File): Promise<Record<string, any>[]> => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = (event) => {
          try {
            const csv = event.target?.result as string;
            const results = Papa.parse(csv, {
              header: true,
              dynamicTyping: false,
              skipEmptyLines: true,
            });
            resolve(results.data as Record<string, any>[]);
          } catch (error) {
            reject(new Error(`CSV parse error: ${error instanceof Error ? error.message : 'Unknown error'}`));
          }
        };

        reader.onerror = () => {
          reject(new Error('Failed to read file'));
        };

        reader.readAsText(file);
      });
    },
    []
  );

  /**
   * Load and process all 4 CSV files
   */
  const loadData = useCallback(
    async (files: {
      accounts: File;
      products: File;
      salesTeams: File;
      pipeline: File;
    }): Promise<ParseResult> => {
      setIsLoading(true);
      const newErrors: string[] = [];

      try {
        // Parse all files
        const [accountsRaw, productsRaw, salesTeamsRaw, pipelineRaw] = await Promise.all([
          parseCSV(files.accounts),
          parseCSV(files.products),
          parseCSV(files.salesTeams),
          parseCSV(files.pipeline),
        ]);

        // Validate columns
        const accountsValidation = validateColumns(accountsRaw, REQUIRED_COLUMNS.accounts);
        if (!accountsValidation.valid) {
          newErrors.push(`accounts.csv: Missing columns: ${accountsValidation.missingColumns.join(', ')}`);
        }

        const productsValidation = validateColumns(productsRaw, REQUIRED_COLUMNS.products);
        if (!productsValidation.valid) {
          newErrors.push(`products.csv: Missing columns: ${productsValidation.missingColumns.join(', ')}`);
        }

        const salesTeamsValidation = validateColumns(salesTeamsRaw, REQUIRED_COLUMNS.salesTeams);
        if (!salesTeamsValidation.valid) {
          newErrors.push(`sales_teams.csv: Missing columns: ${salesTeamsValidation.missingColumns.join(', ')}`);
        }

        const pipelineValidation = validateColumns(pipelineRaw, REQUIRED_COLUMNS.pipeline);
        if (!pipelineValidation.valid) {
          newErrors.push(`sales_pipeline.csv: Missing columns: ${pipelineValidation.missingColumns.join(', ')}`);
        }

        if (newErrors.length > 0) {
          setErrors(newErrors);
          setIsLoading(false);
          return {
            accounts: [],
            products: [],
            salesTeams: [],
            pipeline: [],
            errors: newErrors,
          };
        }

        // Normalize data
        const accounts = accountsRaw
          .map((row) => normalizeAccount(row))
          .filter((acc): acc is Account => acc !== null);

        const products = productsRaw
          .map((row) => normalizeProduct(row))
          .filter((prod): prod is Product => prod !== null);

        const salesTeams = salesTeamsRaw
          .map((row) => normalizeSalesTeamMember(row))
          .filter((team): team is SalesTeam => team !== null);

        const pipeline = pipelineRaw
          .map((row) => normalizePipelineOpportunity(row))
          .filter((opp): opp is PipelineOpportunity => opp !== null);

        // Validation checks
        if (accounts.length === 0) {
          newErrors.push('No valid accounts found in accounts.csv');
        }
        if (products.length === 0) {
          newErrors.push('No valid products found in products.csv');
        }
        if (salesTeams.length === 0) {
          newErrors.push('No valid sales team members found in sales_teams.csv');
        }
        if (pipeline.length === 0) {
          newErrors.push('No valid pipeline opportunities found in sales_pipeline.csv');
        }

        setErrors(newErrors);
        setIsLoading(false);

        return {
          accounts,
          products,
          salesTeams,
          pipeline,
          errors: newErrors,
        };
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        newErrors.push(`Data loading error: ${errorMsg}`);
        setErrors(newErrors);
        setIsLoading(false);

        return {
          accounts: [],
          products: [],
          salesTeams: [],
          pipeline: [],
          errors: newErrors,
        };
      }
    },
    [parseCSV]
  );

  return {
    loadData,
    isLoading,
    errors,
  };
}
