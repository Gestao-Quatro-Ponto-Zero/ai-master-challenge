import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Upload, BarChart3, Users } from 'lucide-react';
import { usePipelineStore } from '@/store/pipeline-store';

const Index = () => {
  const navigate = useNavigate();
  const isDataLoaded = usePipelineStore((s) => s.isDataLoaded());

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-12 px-4">
      <div className="text-center space-y-4">
        <h1 className="font-display text-5xl font-800 tracking-tight text-primary">
          Pipeline Coach AI
        </h1>
        <p className="text-muted-foreground text-lg max-w-md mx-auto">
          Assistente operacional de pipeline para times de vendas B2B.
          Acelere sua performance.
        </p>
      </div>

      {!isDataLoaded && (
        <Button
          size="lg"
          onClick={() => navigate('/upload')}
          className="gap-2 text-base h-14 px-8"
        >
          <Upload className="h-5 w-5" />
          Carregar dados CSV
        </Button>
      )}

      {isDataLoaded && (
        <div className="flex flex-col sm:flex-row gap-4">
          <Button
            size="lg"
            onClick={() => navigate('/rep')}
            className="gap-2 text-base h-14 px-8"
          >
            <BarChart3 className="h-5 w-5" />
            Sou Vendedor
          </Button>
          <Button
            size="lg"
            variant="outline"
            onClick={() => navigate('/manager')}
            className="gap-2 text-base h-14 px-8"
          >
            <Users className="h-5 w-5" />
            Sou Gestor
          </Button>
        </div>
      )}

      {isDataLoaded && (
        <button
          onClick={() => navigate('/upload')}
          className="text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground transition-colors"
        >
          Recarregar dados CSV
        </button>
      )}
    </div>
  );
};

export default Index;
