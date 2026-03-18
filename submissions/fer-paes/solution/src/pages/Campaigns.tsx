import { useState, useEffect, useCallback } from 'react';
import { Megaphone, Plus, Loader2, FileText, Clock, Play, CheckCircle2, PauseCircle } from 'lucide-react';
import {
  getCampaigns,
  type Campaign,
  type CampaignStatus,
} from '../services/campaignService';
import CampaignsTable       from '../components/campaigns/CampaignsTable';
import CampaignCreateModal  from '../components/campaigns/CampaignCreateModal';
import CampaignDetails      from '../components/campaigns/CampaignDetails';

type FilterStatus = 'all' | CampaignStatus;

const STATUS_TABS: { value: FilterStatus; label: string }[] = [
  { value: 'all',       label: 'Todas' },
  { value: 'draft',     label: 'Rascunho' },
  { value: 'scheduled', label: 'Agendadas' },
  { value: 'running',   label: 'Rodando' },
  { value: 'paused',    label: 'Pausadas' },
  { value: 'completed', label: 'Concluídas' },
];

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label:  string;
  value:  number;
  icon:   React.ComponentType<{ className?: string }>;
  color:  string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 px-5 py-4 flex items-center gap-3">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
        <Icon className="w-4 h-4 text-current" />
      </div>
      <div>
        <p className="text-xs text-gray-400">{label}</p>
        <p className="text-xl font-bold text-gray-900 tabular-nums">{value}</p>
      </div>
    </div>
  );
}

export default function Campaigns() {
  const [campaigns,        setCampaigns]        = useState<Campaign[]>([]);
  const [loading,          setLoading]          = useState(true);
  const [error,            setError]            = useState('');
  const [activeFilter,     setActiveFilter]     = useState<FilterStatus>('all');
  const [showCreate,       setShowCreate]       = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const data = await getCampaigns();
      setCampaigns(data);
      if (selectedCampaign) {
        const updated = data.find((c) => c.id === selectedCampaign.id);
        if (updated) setSelectedCampaign(updated);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar campanhas.');
    } finally {
      setLoading(false);
    }
  }, [selectedCampaign]);

  useEffect(() => { load(); }, []);

  async function handleCreated(id: string) {
    setShowCreate(false);
    await load();
  }

  const filtered = activeFilter === 'all'
    ? campaigns
    : campaigns.filter((c) => c.status === activeFilter);

  const stats = {
    total:     campaigns.length,
    scheduled: campaigns.filter((c) => c.status === 'scheduled').length,
    running:   campaigns.filter((c) => c.status === 'running').length,
    completed: campaigns.filter((c) => c.status === 'completed').length,
    draft:     campaigns.filter((c) => c.status === 'draft').length,
    paused:    campaigns.filter((c) => c.status === 'paused').length,
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50 overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-8 py-5 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
              <Megaphone className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Gerenciamento de Campanhas</h1>
              <p className="text-sm text-gray-400">Crie e controle campanhas de comunicação com seus clientes</p>
            </div>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 h-9 px-4 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nova campanha
          </button>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-5 min-h-0">
        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total de campanhas" value={stats.total}     icon={Megaphone}    color="bg-blue-50 text-blue-600"     />
          <StatCard label="Agendadas"           value={stats.scheduled} icon={Clock}         color="bg-sky-50 text-sky-600"       />
          <StatCard label="Rodando"             value={stats.running}   icon={Play}          color="bg-emerald-50 text-emerald-600" />
          <StatCard label="Concluídas"          value={stats.completed} icon={CheckCircle2}  color="bg-teal-50 text-teal-600"     />
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-1 bg-white rounded-xl border border-gray-100 p-1 w-fit">
          {STATUS_TABS.map((tab) => {
            const count = tab.value === 'all'
              ? campaigns.length
              : campaigns.filter((c) => c.status === tab.value).length;
            return (
              <button
                key={tab.value}
                onClick={() => setActiveFilter(tab.value)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  activeFilter === tab.value
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tab.label}
                {count > 0 && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
                    activeFilter === tab.value
                      ? 'bg-white/20 text-white'
                      : 'bg-gray-100 text-gray-500'
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Main area */}
        <div className="flex gap-5 items-start">
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center gap-2">
              <Megaphone className="w-4 h-4 text-gray-400" />
              <h2 className="text-sm font-semibold text-gray-700">Campanhas</h2>
              {loading && <Loader2 className="w-3.5 h-3.5 text-gray-300 animate-spin ml-1" />}
              <span className="text-xs text-gray-400 ml-1">{filtered.length} resultado{filtered.length !== 1 ? 's' : ''}</span>
            </div>
            <CampaignsTable
              campaigns={filtered}
              loading={loading}
              selectedId={selectedCampaign?.id}
              onSelect={(c) => setSelectedCampaign((prev) => prev?.id === c.id ? null : c)}
              onRefresh={load}
            />
          </div>

          {selectedCampaign && (
            <div className="w-[400px] shrink-0 sticky top-0">
              <CampaignDetails
                campaign={selectedCampaign}
                onClose={() => setSelectedCampaign(null)}
                onRefresh={load}
              />
            </div>
          )}
        </div>
      </div>

      {showCreate && (
        <CampaignCreateModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  );
}
