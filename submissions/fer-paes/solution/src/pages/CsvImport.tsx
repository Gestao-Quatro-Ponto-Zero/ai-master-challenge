import { useState, useRef, useCallback } from 'react';
import {
  Upload, FileText, CheckCircle2, XCircle, AlertCircle,
  RotateCcw, ChevronDown, ChevronUp, Download,
} from 'lucide-react';
import {
  importCsv,
  REQUIRED_COLUMNS,
  type CsvImportProgress,
} from '../services/csvImportService';

const EXAMPLE_COLUMNS = [
  'Ticket ID', 'Customer Name', 'Customer Email', 'Customer Age',
  'Customer Gender', 'Product Purchased', 'Date of Purchase',
  'Ticket Type', 'Ticket Subject', 'Ticket Description',
  'Ticket Status', 'Resolution', 'Ticket Priority', 'Ticket Channel',
  'First Response Time', 'Time to Resolution', 'Customer Satisfaction Rating',
];

function ProgressBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.07)' }}>
      <div
        className="h-full rounded-full transition-all duration-300"
        style={{
          width: `${pct}%`,
          background: 'linear-gradient(90deg, #00aeff, #3fffff)',
          boxShadow: pct > 0 ? '0 0 12px rgba(0,174,255,0.5)' : 'none',
        }}
      />
    </div>
  );
}

function StatCard({
  label, value, color,
}: { label: string; value: number; color: string }) {
  return (
    <div
      className="flex-1 rounded-xl p-4 text-center"
      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
    >
      <p className="text-2xl font-bold" style={{ color }}>{value.toLocaleString()}</p>
      <p className="text-xs text-slate-500 mt-1">{label}</p>
    </div>
  );
}

export default function CsvImport() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<CsvImportProgress | null>(null);
  const [showErrors, setShowErrors] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (f: File) => {
    if (!f.name.endsWith('.csv') && f.type !== 'text/csv') {
      alert('Por favor selecione um arquivo .csv');
      return;
    }
    setFile(f);
    setProgress(null);
    setShowErrors(false);
  };

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const onDragLeave = useCallback(() => setDragging(false), []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  async function startImport() {
    if (!file) return;
    setProgress({
      total: 0, processed: 0, inserted: 0,
      updated: 0, errors: 0, errorDetails: [], phase: 'parsing',
    });
    await importCsv(file, (p) => setProgress({ ...p }));
  }

  function reset() {
    setFile(null);
    setProgress(null);
    setShowErrors(false);
    if (inputRef.current) inputRef.current.value = '';
  }

  const isDone = progress?.phase === 'done';
  const isRunning = progress?.phase === 'parsing' || progress?.phase === 'importing';
  const pct = progress && progress.total > 0
    ? Math.round((progress.processed / progress.total) * 100)
    : 0;

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">Importar CSV</h1>
        <p className="text-slate-500 text-sm">
          Importe tickets e clientes a partir de um arquivo CSV. Registros existentes
          serão atualizados com base no Ticket ID original.
        </p>
      </div>

      {!progress && (
        <>
          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            className="relative rounded-2xl cursor-pointer transition-all duration-200 p-10 flex flex-col items-center justify-center gap-4"
            style={{
              border: `2px dashed ${dragging ? '#00aeff' : file ? '#3fffff' : 'rgba(255,255,255,0.12)'}`,
              background: dragging
                ? 'rgba(0,174,255,0.06)'
                : file
                ? 'rgba(63,255,255,0.04)'
                : 'rgba(255,255,255,0.02)',
              minHeight: 220,
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
            />
            {file ? (
              <>
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center"
                  style={{ background: 'rgba(63,255,255,0.1)', border: '1px solid rgba(63,255,255,0.2)' }}
                >
                  <FileText className="w-7 h-7" style={{ color: '#3fffff' }} />
                </div>
                <div className="text-center">
                  <p className="text-white font-semibold text-sm">{file.name}</p>
                  <p className="text-slate-500 text-xs mt-1">
                    {(file.size / 1024 / 1024).toFixed(1)} MB — clique para trocar
                  </p>
                </div>
              </>
            ) : (
              <>
                <div
                  className="w-16 h-16 rounded-2xl flex items-center justify-center"
                  style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
                >
                  <Upload className="w-7 h-7 text-slate-500" />
                </div>
                <div className="text-center">
                  <p className="text-slate-300 font-medium text-sm">
                    Arraste o arquivo CSV aqui
                  </p>
                  <p className="text-slate-600 text-xs mt-1">
                    ou clique para selecionar — até 50 MB
                  </p>
                </div>
              </>
            )}
          </div>

          <div
            className="mt-4 rounded-xl p-4"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
              Colunas esperadas no CSV
            </p>
            <div className="flex flex-wrap gap-1.5">
              {EXAMPLE_COLUMNS.map((col) => {
                const required = REQUIRED_COLUMNS.includes(col);
                return (
                  <span
                    key={col}
                    className="px-2 py-0.5 rounded-md text-xs font-mono"
                    style={{
                      background: required ? 'rgba(0,174,255,0.1)' : 'rgba(255,255,255,0.04)',
                      border: `1px solid ${required ? 'rgba(0,174,255,0.25)' : 'rgba(255,255,255,0.08)'}`,
                      color: required ? '#00aeff' : '#64748b',
                    }}
                  >
                    {col}
                  </span>
                );
              })}
            </div>
            <p className="text-[11px] text-slate-600 mt-3">
              <span style={{ color: '#00aeff' }}>Azul</span> = obrigatório.
              Os separadores aceitos são vírgula (,) e tabulação (tab).
            </p>
          </div>

          {file && (
            <button
              onClick={startImport}
              className="mt-6 w-full py-3.5 rounded-xl font-semibold text-sm text-white transition-all duration-200 hover:opacity-90 active:scale-[0.99]"
              style={{
                background: 'linear-gradient(90deg, #00aeff, #3fffff)',
                boxShadow: '0 0 24px rgba(0,174,255,0.3)',
              }}
            >
              Iniciar importação
            </button>
          )}
        </>
      )}

      {progress && (
        <div
          className="rounded-2xl p-6"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
        >
          <div className="flex items-center gap-3 mb-5">
            {isDone ? (
              progress.errors === progress.total && progress.total > 0 ? (
                <XCircle className="w-6 h-6 shrink-0" style={{ color: '#f87171' }} />
              ) : progress.errors > 0 ? (
                <AlertCircle className="w-6 h-6 shrink-0" style={{ color: '#fbbf24' }} />
              ) : (
                <CheckCircle2 className="w-6 h-6 shrink-0" style={{ color: '#34d399' }} />
              )
            ) : (
              <div
                className="w-6 h-6 rounded-full border-2 border-t-transparent animate-spin shrink-0"
                style={{ borderColor: '#00aeff', borderTopColor: 'transparent' }}
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-white font-semibold text-sm">
                {progress.phase === 'parsing' && 'Lendo arquivo CSV…'}
                {progress.phase === 'importing' && `Importando… ${pct}%`}
                {isDone && 'Importação concluída'}
                {progress.phase === 'error' && 'Erro ao processar arquivo'}
              </p>
              {progress.total > 0 && (
                <p className="text-xs text-slate-500 mt-0.5">
                  {progress.processed.toLocaleString()} de {progress.total.toLocaleString()} linhas
                </p>
              )}
            </div>
            <span className="text-lg font-bold" style={{ color: '#00aeff' }}>{pct}%</span>
          </div>

          <ProgressBar value={progress.processed} max={progress.total} />

          {progress.total > 0 && (
            <div className="flex gap-3 mt-5">
              <StatCard label="Inseridos" value={progress.inserted} color="#34d399" />
              <StatCard label="Atualizados" value={progress.updated} color="#60a5fa" />
              <StatCard label="Erros" value={progress.errors} color="#f87171" />
              <StatCard
                label="Total"
                value={progress.total}
                color="#94a3b8"
              />
            </div>
          )}

          {isDone && progress.errorDetails.length > 0 && (
            <div className="mt-5">
              <button
                onClick={() => setShowErrors((v) => !v)}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
              >
                {showErrors ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {showErrors ? 'Ocultar' : 'Ver'} {progress.errorDetails.length} mensagem(s) de erro
              </button>
              {showErrors && (
                <div
                  className="mt-3 rounded-xl p-3 max-h-48 overflow-y-auto space-y-1"
                  style={{ background: 'rgba(248,113,113,0.06)', border: '1px solid rgba(248,113,113,0.15)' }}
                >
                  {progress.errorDetails.map((e, i) => (
                    <p key={i} className="text-xs font-mono text-red-400">{e}</p>
                  ))}
                </div>
              )}
            </div>
          )}

          {isDone && (
            <button
              onClick={reset}
              className="mt-5 w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-all hover:bg-white/5"
              style={{ border: '1px solid rgba(255,255,255,0.08)' }}
            >
              <RotateCcw className="w-4 h-4" />
              Importar outro arquivo
            </button>
          )}
        </div>
      )}

      <div
        className="mt-6 rounded-xl p-4 flex items-start gap-3"
        style={{ background: 'rgba(251,191,36,0.05)', border: '1px solid rgba(251,191,36,0.15)' }}
      >
        <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#fbbf24' }} />
        <div>
          <p className="text-xs font-semibold text-yellow-400 mb-1">Comportamento da reimportação</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            Se um <strong className="text-slate-400">Ticket ID</strong> já existir no banco, o registro
            será <strong className="text-slate-400">atualizado</strong> — não duplicado.
            Clientes são identificados pelo e-mail: se o e-mail já existir, nome e dados serão atualizados.
          </p>
        </div>
      </div>
    </div>
  );
}
