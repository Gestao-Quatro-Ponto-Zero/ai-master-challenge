import React from 'react';
import { Globe } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="flex items-center gap-2">
      <Globe className="w-4 h-4" />
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="px-3 py-1 rounded text-sm font-medium bg-slate-700 text-white border border-slate-600 hover:bg-slate-600 transition-colors cursor-pointer"
      >
        <option value="en">English</option>
        <option value="pt-BR">Português (BR)</option>
      </select>
    </div>
  );
}
