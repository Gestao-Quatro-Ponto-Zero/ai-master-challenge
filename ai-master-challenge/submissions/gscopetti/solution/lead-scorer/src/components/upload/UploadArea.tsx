import { useState } from 'react';
import { useDataLoader } from '@/hooks/useDataLoader';
import { useDataContext, dataActions } from '@/context/DataContext';
import { ScoringValidation } from '@/components/dashboard/ScoringValidation';
import { Card, Button } from '@/components/ui';

export function UploadArea() {
  const { loadData, isLoading, errors } = useDataLoader();
  const { dispatch } = useDataContext();

  const [files, setFiles] = useState<{
    accounts?: File;
    products?: File;
    salesTeams?: File;
    pipeline?: File;
  }>({});

  const handleFileChange = (fileType: string, file: File | null) => {
    if (file) {
      setFiles((prev) => ({ ...prev, [fileType]: file }));
    }
  };

  const handleUpload = async () => {
    if (!files.accounts || !files.products || !files.salesTeams || !files.pipeline) {
      alert('Please select all 4 CSV files');
      return;
    }

    const result = await loadData({
      accounts: files.accounts,
      products: files.products,
      salesTeams: files.salesTeams,
      pipeline: files.pipeline,
    });

    if (result.errors.length === 0) {
      dispatch(dataActions.loadData(result.accounts, result.products, result.salesTeams, result.pipeline));
      alert(`✅ Data loaded successfully!\nAccounts: ${result.accounts.length}\nProducts: ${result.products.length}\nSales Teams: ${result.salesTeams.length}\nOpportunities: ${result.pipeline.length}`);

      // Log to console for verification
      console.log('📊 Loaded Data:');
      console.log('Accounts:', result.accounts.slice(0, 5));
      console.log('Products:', result.products);
      console.log('Sales Teams:', result.salesTeams.slice(0, 5));
      console.log('Pipeline (first 5):', result.pipeline.slice(0, 5));
    } else {
      alert(`❌ Errors loading data:\n${result.errors.join('\n')}`);
    }
  };

  const { state } = useDataContext();

  // Show validation if data is loaded
  if (state.isLoaded) {
    return (
      <div className="space-y-12 animate-in fade-in duration-500">
        <Card variant="default" padding="lg" className="border-t-4 border-t-hubspot-orange text-center shadow-xl bg-white">
          <div className="w-20 h-20 bg-hubspot-orange text-white rounded-full flex items-center justify-center mx-auto mb-6 text-3xl font-black">
            ✓
          </div>
          <h2 className="text-3xl font-black text-hubspot-black mb-2 tracking-tighter uppercase">Inteligência Ativada</h2>
          <p className="text-hubspot-black/60 font-bold mb-10 text-lg uppercase tracking-widest">Pipeline processado com sucesso</p>
          <Button
            variant="secondary"
            size="md"
            onClick={() => dispatch(dataActions.resetData())}
            className="uppercase tracking-widest text-[10px] font-black border-2"
          >
            ← Resetar & Carregar Novos Dados
          </Button>
        </Card>
        <ScoringValidation />
      </div>
    );
  }

  return (
    <Card variant="default" padding="lg" className="bg-white border-hubspot-gray-200 shadow-2xl overflow-hidden max-w-4xl mx-auto">
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-black text-hubspot-black tracking-tighter mb-2 uppercase">
          Upload de Inteligência
        </h2>
        <div className="h-1 w-20 bg-hubspot-orange mx-auto rounded-full mb-4" />
        <p className="text-hubspot-black/60 font-bold text-sm uppercase tracking-widest px-10">Conecte seus arquivos CSV para ativar o motor de scoring preditivo.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {[
          { id: 'accounts', label: 'ACCOUNTS.CSV', icon: '🏢' },
          { id: 'products', label: 'PRODUCTS.CSV', icon: '📦' },
          { id: 'salesTeams', label: 'SALES_TEAMS.CSV', icon: '👥' },
          { id: 'pipeline', label: 'PIPELINE.CSV', icon: '🎯' }
        ].map((field) => (
          <div key={field.id} className="group">
            <label className="block text-[10px] font-black text-hubspot-black uppercase tracking-[0.2em] mb-3 ml-1">
              {field.label}
            </label>
            <div className={`relative border-2 rounded-hb p-8 transition-all duration-200 ${(files as any)[field.id] ? 'bg-green-50 border-green-500' : 'bg-hubspot-gray-100/50 border-hubspot-gray-200 group-hover:border-hubspot-orange group-hover:bg-white shadow-sm'}`}>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => handleFileChange(field.id, e.target.files?.[0] || null)}
                disabled={isLoading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="text-center">
                {(files as any)[field.id] ? (
                  <p className="text-sm font-black text-green-700 truncate max-w-full italic">PRONTO: {(files as any)[field.id].name}</p>
                ) : (
                  <div className="flex flex-col items-center gap-2">
                    <p className="text-[10px] font-black text-hubspot-black/30 uppercase tracking-[0.2em] group-hover:text-hubspot-orange transition-colors">Selecionar Arquivo</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={handleUpload}
        disabled={isLoading}
        className="group relative w-full overflow-hidden rounded-hb bg-hubspot-orange p-8 text-white transition-all hover:bg-hubspot-black disabled:bg-hubspot-gray-200 active:scale-[0.98] shadow-2xl shadow-hubspot-orange/20"
      >
        <span className="relative z-10 text-base font-black uppercase tracking-[0.4em] flex items-center justify-center gap-3">
          {isLoading ? '⏳ Processando Inteligência...' : 'Gerar Scoring de Pipeline'}
        </span>
      </button>

      {errors.length > 0 && (
        <div className="mt-8 p-6 bg-red-50 border-l-4 border-red-600 rounded-r-hb">
          <p className="text-red-700 text-[10px] font-black uppercase tracking-widest mb-3">
            ⚠️ FALHA NO PROCESSAMENTO:
          </p>
          <div className="space-y-1">
            {errors.map((error, i) => (
              <p key={i} className="text-xs font-bold text-red-800">• {error}</p>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
