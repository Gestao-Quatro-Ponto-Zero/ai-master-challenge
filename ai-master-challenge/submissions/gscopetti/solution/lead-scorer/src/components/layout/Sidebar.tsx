import { useState } from 'react';
import { Menu, X } from 'lucide-react';

interface SidebarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

export function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

  const pages = [
    { id: 'upload', label: 'Upload' },
    { id: 'dashboard', label: 'Painel' },
    { id: 'deals', label: 'Deals' },
    { id: 'accounts', label: 'Contas' },
    { id: 'team', label: 'Time' },
  ];

  const handlePageChange = (page: string) => {
    onPageChange(page);
    setIsOpen(false);
  };

  return (
    <>
      {/* Mobile Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg bg-white border border-hubspot-gray-200 text-hubspot-black shadow-md"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Sidebar */}
      <aside
        className={`fixed lg:static top-0 left-0 h-screen w-72 bg-white border-r border-hubspot-gray-200 z-40 transform lg:transform-none transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          }`}
      >
        {/* Header */}
        <div className="p-10 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-hubspot-orange flex items-center justify-center text-white text-xl font-black">
              H
            </div>
            <div>
              <h1 className="font-extrabold text-hubspot-black text-lg tracking-tight leading-none uppercase">Lead Scorer</h1>
              <p className="text-[9px] font-black text-hubspot-orange uppercase tracking-[0.2em] mt-1">Intelligence</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="px-6 space-y-1">
          {pages.map((page) => (
            <button
              key={page.id}
              onClick={() => handlePageChange(page.id)}
              className={`w-full text-left px-4 py-3.5 rounded-hb transition-all duration-200 font-bold text-sm tracking-wide ${currentPage === page.id
                ? 'bg-hubspot-orange/5 text-hubspot-orange border-r-4 border-hubspot-orange'
                : 'text-hubspot-black/60 hover:bg-hubspot-gray-100 hover:text-hubspot-black uppercase tracking-widest text-[11px]'
                }`}
            >
              {page.label}
            </button>
          ))}
        </nav>

        {/* Quick Stats / Tip - Simplified */}
        <div className="mt-auto p-6 mb-20">
          <div className="p-6 rounded-hb bg-hubspot-black text-white shadow-2xl">
            <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em] mb-3">Estratégia</p>
            <p className="text-xs text-white leading-relaxed font-bold italic">
              Priorize leads <span className="text-white underline decoration-2 underline-offset-4 font-black">HOT</span> para otimizar conversão imediata.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-hubspot-gray-100 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-black text-hubspot-black/40 uppercase tracking-widest">v2.1 PRO</span>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span className="text-[9px] font-bold text-green-700 uppercase tracking-tighter">Status: Ativo</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-30 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
