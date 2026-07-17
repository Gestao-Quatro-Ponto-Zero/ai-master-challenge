import React, { useState } from 'react';
import { ChevronRight, Zap, AlertTriangle, X } from 'lucide-react';

export default function DealRow({ deal }: { deal: any }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const hasHotSignal = deal.tags?.includes('🔥 SINAL QUENTE');
  const isStagnated = deal.tags?.includes('🚨 ESTAGNADO') || deal.tags?.includes('🚨 SEM RESPOSTA');

  return (
    <>
      <div 
        onClick={() => setIsModalOpen(true)}
        className="grid grid-cols-12 gap-4 items-center p-4 bg-white border border-gray-100 rounded-xl hover:shadow-md hover:border-blue-200 transition-all cursor-pointer mb-3"
      >
        <div className="col-span-3 flex flex-col">
          <span className="font-bold text-gray-900">{deal.account || 'Empresa Desconhecida'}</span>
          <span className="text-xs text-gray-500">{deal.sector || 'N/A'}</span>
        </div>
        
        <div className="col-span-3 flex flex-col">
          <span className="text-sm font-medium text-gray-700">{deal.product}</span>
          <span className="text-xs text-gray-400">Produto</span>
        </div>
        
        <div className="col-span-2 flex flex-col">
          <span className="text-sm font-bold text-gray-800">
            {deal.valor_esperado ? `$${deal.valor_esperado.toLocaleString()}` : '-'}
          </span>
          <span className="text-xs text-gray-400">Valor Esperado</span>
        </div>
        
        <div className="col-span-2 flex items-center gap-2">
          {hasHotSignal && <span className="bg-orange-100 text-orange-600 px-2 py-1 rounded-md text-xs font-bold flex items-center gap-1"><Zap size={12}/> Quente</span>}
          {isStagnated && <span className="bg-red-100 text-red-600 px-2 py-1 rounded-md text-xs font-bold flex items-center gap-1"><AlertTriangle size={12}/> Risco</span>}
          {!hasHotSignal && !isStagnated && <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded-md text-xs font-medium">{deal.deal_stage}</span>}
        </div>
        
        <div className="col-span-1 flex justify-center">
          <span className={`px-3 py-1 rounded-lg font-bold border ${getScoreColor(deal.pontuacao)}`}>
            {deal.pontuacao}
          </span>
        </div>
        
        <div className="col-span-1 flex justify-end text-gray-400">
          <ChevronRight size={20} />
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col">
            <div className="p-6 border-b border-gray-100 flex justify-between items-start">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{deal.account}</h2>
                <p className="text-gray-500">{deal.product} • Fechamento estimado em {deal.dias_no_funil} dias</p>
              </div>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-900 bg-gray-100 p-2 rounded-full transition-colors">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 bg-gray-50 flex-1">
              <div className="flex gap-4 mb-6">
                <div className={`p-4 rounded-xl border ${getScoreColor(deal.pontuacao)} w-32 flex flex-col items-center justify-center`}>
                  <span className="text-3xl font-black">{deal.pontuacao}</span>
                  <span className="text-xs uppercase font-bold tracking-wider">Score AI</span>
                </div>
                <div className="flex-1 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Ação Recomendada (Estratégia)</h4>
                  <p className="text-blue-700 font-medium">{deal.acao_sugerida}</p>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="bg-gray-100 px-4 py-2 border-b border-gray-200">
                  <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Explainability Engine (Motivos)</h4>
                </div>
                <ul className="p-4 space-y-3">
                  {deal.explicacoes.map((exp: string, idx: number) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="mt-0.5">{exp.charAt(0)}</span>
                      <span>{exp.substring(1)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="p-6 border-t border-gray-100 flex justify-end gap-3 bg-white">
              <button onClick={() => setIsModalOpen(false)} className="px-6 py-2 rounded-lg font-medium text-gray-600 hover:bg-gray-100 transition-colors">
                Fechar
              </button>
              {(hasHotSignal || deal.tags?.includes('🚨 SEM RESPOSTA')) && (
                <button className="px-6 py-2 rounded-lg font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-md flex items-center gap-2 transition-all">
                  <Zap size={16} /> Acionar IA Auto-Responder
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
