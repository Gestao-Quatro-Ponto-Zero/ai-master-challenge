import React from 'react';
import { Home, PieChart, Users, Settings, LogOut, Briefcase } from 'lucide-react';

export default function Sidebar() {
  return (
    <div className="w-64 bg-white border-r border-gray-200 h-screen fixed left-0 top-0 flex flex-col items-center py-6 shadow-sm z-50">
      {/* Logo */}
      <div className="mb-10 w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-md">
        P
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-4 w-full px-4">
        <button className="flex items-center gap-3 px-4 py-3 bg-blue-50 text-blue-700 rounded-xl font-semibold transition-colors">
          <PieChart size={20} />
          <span>Dashboard</span>
        </button>
        <button className="flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-gray-50 hover:text-gray-900 rounded-xl font-medium transition-colors">
          <Briefcase size={20} />
          <span>Oportunidades</span>
        </button>
        <button className="flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-gray-50 hover:text-gray-900 rounded-xl font-medium transition-colors">
          <Users size={20} />
          <span>Equipe</span>
        </button>
      </nav>

      <div className="mt-auto flex flex-col w-full px-4 gap-2">
        <button className="flex items-center gap-3 px-4 py-3 text-gray-500 hover:bg-gray-50 hover:text-gray-900 rounded-xl font-medium transition-colors">
          <Settings size={20} />
          <span>Configurações</span>
        </button>
        <div className="w-full border-t border-gray-100 my-2"></div>
        <div className="flex items-center gap-3 px-4 py-2 mt-2">
          <div className="w-10 h-10 bg-gray-200 rounded-full overflow-hidden">
            <img src="https://i.pravatar.cc/150?u=a042581f4e29026704d" alt="User" />
          </div>
          <div className="flex flex-col text-sm">
            <span className="font-bold text-gray-800">Darcel S.</span>
            <span className="text-gray-400 text-xs">Vendas G4</span>
          </div>
        </div>
      </div>
    </div>
  );
}
