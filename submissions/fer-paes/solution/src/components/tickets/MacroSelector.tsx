import { useEffect, useRef, useState } from 'react';
import { Zap, ChevronRight } from 'lucide-react';
import { getMacros } from '../../services/macroService';
import type { Macro } from '../../types';

interface Props {
  query: string;
  onSelect: (macro: Macro) => void;
  onClose: () => void;
}

export default function MacroSelector({ query, onSelect, onClose }: Props) {
  const [macros, setMacros] = useState<Macro[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMacros().then(setMacros).catch(() => {});
  }, []);

  const filtered = macros.filter(
    (m) =>
      !query ||
      m.name.toLowerCase().includes(query.toLowerCase()) ||
      m.category.toLowerCase().includes(query.toLowerCase()),
  );

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[activeIndex]) onSelect(filtered[activeIndex]);
      } else if (e.key === 'Escape') {
        onClose();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [filtered, activeIndex, onSelect, onClose]);

  useEffect(() => {
    const el = listRef.current?.children[activeIndex] as HTMLElement | undefined;
    el?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  if (filtered.length === 0) return null;

  const grouped = filtered.reduce<Record<string, Macro[]>>((acc, m) => {
    const cat = m.category || 'General';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(m);
    return acc;
  }, {});

  let globalIndex = 0;

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 mx-2 z-40 bg-white rounded-2xl border border-gray-200 shadow-xl shadow-gray-100/80 overflow-hidden max-h-64 flex flex-col">
      <div className="px-3 py-2 border-b border-gray-100 flex items-center gap-2 shrink-0">
        <Zap className="w-3 h-3 text-blue-500" />
        <span className="text-[11px] font-semibold text-gray-500 uppercase tracking-wide">Macros</span>
        {query && <span className="text-[11px] text-gray-400">— "{query}"</span>}
        <span className="ml-auto text-[10px] text-gray-400">↑↓ navigate · Enter select · Esc close</span>
      </div>

      <div ref={listRef} className="overflow-y-auto flex-1">
        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat}>
            <p className="px-3 py-1.5 text-[10px] font-bold text-gray-400 uppercase tracking-wide bg-gray-50/80 sticky top-0">
              {cat}
            </p>
            {items.map((macro) => {
              const idx = globalIndex++;
              const isActive = idx === activeIndex;
              return (
                <button
                  key={macro.id}
                  onMouseEnter={() => setActiveIndex(idx)}
                  onClick={() => onSelect(macro)}
                  className={`w-full text-left px-3 py-2.5 flex items-start gap-3 transition-colors ${
                    isActive ? 'bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-semibold truncate ${isActive ? 'text-blue-700' : 'text-gray-800'}`}>
                      {macro.name}
                    </p>
                    <p className="text-[11px] text-gray-400 truncate mt-0.5 leading-snug">
                      {macro.content.replace(/\{\{[^}]+\}\}/g, (m) => m.slice(2, -2))}
                    </p>
                  </div>
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />}
                </button>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
