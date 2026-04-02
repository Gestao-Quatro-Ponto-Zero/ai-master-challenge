import { useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Papa from 'papaparse';
import { usePipelineStore } from '@/store/pipeline-store';
import { EXPECTED_HEADERS, normalizeProduct } from '@/lib/csv-utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Upload as UploadIcon, CheckCircle, XCircle, Clock, Loader2, ArrowRight, AlertTriangle, Home, Database } from 'lucide-react';
import { SAMPLE_PIPELINE, SAMPLE_TEAMS, SAMPLE_PRODUCTS } from '@/lib/sample-data';
import type { PipelineDeal, SalesTeam, Product, Account, Metadata } from '@/types/csv';

const FILE_NAMES = [
  'sales_pipeline.csv',
  'sales_teams.csv',
  'products.csv',
  'accounts.csv',
  'metadata.csv',
] as const;

const statusIcons: Record<string, React.ReactNode> = {
  waiting: <Clock className="h-4 w-4 text-muted-foreground" />,
  processing: <Loader2 className="h-4 w-4 text-engaging animate-spin" />,
  loaded: <CheckCircle className="h-4 w-4 text-won" />,
  error: <XCircle className="h-4 w-4 text-lost" />,
};

const UploadPage = () => {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const store = usePipelineStore();
  const { fileStates, pipeline } = store;

  const pipelineLoaded = fileStates['sales_pipeline.csv']?.status === 'loaded';

  const emptyAccountPct = pipeline.length > 0
    ? ((pipeline.filter(d => !d.account || d.account.trim() === '').length / pipeline.length) * 100).toFixed(1)
    : '0';

  const processFile = useCallback((file: File) => {
    const filename = file.name;
    const expectedHeaders = EXPECTED_HEADERS[filename];

    if (!expectedHeaders) {
      store.setFileState(filename, { status: 'error', rowCount: 0, error: `Arquivo inesperado: ${filename}` });
      return;
    }

    store.setFileState(filename, { status: 'processing', rowCount: 0 });

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const headers = results.meta.fields || [];
        const missing = expectedHeaders.filter(h => !headers.includes(h));

        if (missing.length > 0) {
          store.setFileState(filename, {
            status: 'error',
            rowCount: 0,
            error: `Colunas ausentes: ${missing.join(', ')}`,
          });
          return;
        }

        const data = results.data as Record<string, string>[];

        if (filename === 'sales_pipeline.csv') {
          const normalized = data.map(row => ({
            ...row,
            product: normalizeProduct(row.product || ''),
          })) as unknown as PipelineDeal[];
          store.setPipeline(normalized);
        } else if (filename === 'sales_teams.csv') {
          store.setTeams(data as unknown as SalesTeam[]);
        } else if (filename === 'products.csv') {
          const normalized = data.map(row => ({
            ...row,
            product: normalizeProduct(row.product || ''),
          })) as unknown as Product[];
          store.setProducts(normalized);
        } else if (filename === 'accounts.csv') {
          store.setAccounts(data as unknown as Account[]);
        } else if (filename === 'metadata.csv') {
          store.setMetadata(data as unknown as Metadata[]);
        }

        store.setFileState(filename, { status: 'loaded', rowCount: data.length });
      },
      error: (err) => {
        store.setFileState(filename, { status: 'error', rowCount: 0, error: err.message });
      },
    });
  }, [store]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    files.forEach(processFile);
  }, [processFile]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(processFile);
    e.target.value = '';
  }, [processFile]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-start py-12 px-4">
      <div className="w-full max-w-2xl space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-display text-3xl font-800 text-primary">Upload de Dados</h1>
            <p className="text-muted-foreground mt-1">Carregue os arquivos CSV do CRM para começar.</p>
          </div>
          <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
            <Home className="h-5 w-5" />
          </Button>
        </div>

        {/* Drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="border-2 border-dashed border-border rounded-lg p-12 flex flex-col items-center gap-4 cursor-pointer hover:border-primary/50 transition-colors"
        >
          <UploadIcon className="h-10 w-10 text-muted-foreground" />
          <div className="text-center">
            <p className="font-display text-lg font-700">Arraste seus CSVs aqui</p>
            <p className="text-sm text-muted-foreground mt-1">ou clique para selecionar</p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* Load sample data button */}
        <Button
          variant="outline"
          className="w-full gap-2"
          onClick={() => {
            store.setPipeline(SAMPLE_PIPELINE);
            store.setTeams(SAMPLE_TEAMS);
            store.setProducts(SAMPLE_PRODUCTS);
            store.setFileState('sales_pipeline.csv', { status: 'loaded', rowCount: SAMPLE_PIPELINE.length });
            store.setFileState('sales_teams.csv', { status: 'loaded', rowCount: SAMPLE_TEAMS.length });
            store.setFileState('products.csv', { status: 'loaded', rowCount: SAMPLE_PRODUCTS.length });
          }}
        >
          <Database className="h-4 w-4" />
          Carregar dados de exemplo (teste)
        </Button>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="font-display text-lg">Arquivos Esperados</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {FILE_NAMES.map((name) => {
              const state = fileStates[name] || { status: 'waiting', rowCount: 0 };
              return (
                <div key={name} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <div className="flex items-center gap-3">
                    {statusIcons[state.status]}
                    <span className="text-sm font-mono">{name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {state.status === 'loaded' && (
                      <Badge variant="secondary" className="text-xs">
                        {state.rowCount.toLocaleString()} linhas
                      </Badge>
                    )}
                    {state.status === 'error' && (
                      <span className="text-xs text-lost">{state.error}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Anomaly banner */}
        {pipelineLoaded && (
          <Alert className="border-prospecting/30 bg-prospecting/5">
            <AlertTriangle className="h-4 w-4 text-prospecting" />
            <AlertTitle className="font-display">Dados carregados</AlertTitle>
            <AlertDescription className="space-y-1 text-sm">
              <p>• {pipeline.length.toLocaleString()} deals no pipeline</p>
              <p>• {emptyAccountPct}% com conta não identificada</p>
              <p>• Normalização GTXPro aplicada automaticamente ✓</p>
            </AlertDescription>
          </Alert>
        )}

        {/* Navigate to dashboard */}
        <Button
          size="lg"
          disabled={!pipelineLoaded}
          onClick={() => navigate('/')}
          className="w-full gap-2 h-12"
        >
          Ir para o Dashboard
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default UploadPage;
