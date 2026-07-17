import React from 'react';

export default function DealCard({ deal }: { deal: any }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-xl hover:border-gray-600 transition-all flex flex-col gap-4">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-xl font-bold text-white">{deal.account || 'Unknown Company'}</h3>
          <p className="text-sm text-gray-400">{deal.sector || 'N/A'} • {deal.product}</p>
        </div>
        <div className={`px-4 py-2 rounded-lg font-bold text-lg ${
          deal.score >= 80 ? 'bg-green-900 text-green-300' :
          deal.score >= 50 ? 'bg-yellow-900 text-yellow-300' :
          'bg-red-900 text-red-300'
        }`}>
          {deal.score} pts
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm text-gray-300 border-y border-gray-800 py-3">
        <div><span className="text-gray-500">Value:</span> ${deal.expected_value?.toLocaleString()}</div>
        <div><span className="text-gray-500">Stage:</span> {deal.deal_stage}</div>
        <div><span className="text-gray-500">Days Active:</span> {deal.days_in_pipeline}</div>
        <div><span className="text-gray-500">Agent:</span> {deal.sales_agent}</div>
      </div>

      {deal.tags && deal.tags.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {deal.tags.map((tag: string, idx: number) => (
            <span key={idx} className={`text-xs px-2 py-1 rounded-md font-bold ${
              tag.includes('HOT') ? 'bg-orange-500 text-black' : 'bg-red-950 text-red-400 border border-red-800'
            }`}>
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="bg-gray-950 p-4 rounded-lg text-sm text-gray-400">
        <h4 className="text-white mb-2 font-semibold">Explainability Engine</h4>
        <ul className="space-y-1">
          {deal.explanations.map((exp: string, idx: number) => (
            <li key={idx}>{exp}</li>
          ))}
        </ul>
      </div>

      <div className="mt-auto pt-4 flex flex-col gap-2">
        <p className="text-sm"><span className="text-blue-400 font-bold">Suggested Action:</span> {deal.suggested_action}</p>
        {deal.tags?.includes('HOT SIGNAL') || deal.tags?.includes('GHOSTING') ? (
          <button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded-lg transition-colors">
            Trigger AI Auto-Responder
          </button>
        ) : (
          <button className="w-full bg-gray-800 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-colors border border-gray-700">
            View Details
          </button>
        )}
      </div>
    </div>
  );
}
