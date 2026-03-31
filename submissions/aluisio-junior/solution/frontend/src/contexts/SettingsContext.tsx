import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export interface CLevel {
  id: string;
  nome: string;
  cargo: string;
  email: string;
  whatsapp: string;
  ativo: boolean;
}

export interface AppUser {
  id: string;
  nome: string;
  email: string;
  perfil: string;
  status: "ativo" | "inativo";
  senha?: string;
}

interface SettingsContextType {
  cLevels: CLevel[];
  addCLevel: (c: Omit<CLevel, "id">) => void;
  updateCLevel: (id: string, c: Partial<CLevel>) => void;
  toggleCLevel: (id: string) => void;
  users: AppUser[];
  addUser: (u: Omit<AppUser, "id">) => void;
  updateUser: (id: string, u: Partial<AppUser>) => void;
  toggleUser: (id: string) => void;
}

const CLEVELS_KEY = "churn_intelligence_clevels";
const USERS_KEY = "churn_intelligence_users";

function loadFromStorage<T>(key: string, fallback: T[]): T[] {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

const SettingsContext = createContext<SettingsContextType>({} as SettingsContextType);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [cLevels, setCLevels] = useState<CLevel[]>(() => loadFromStorage<CLevel>(CLEVELS_KEY, []));
  const [users, setUsers] = useState<AppUser[]>(() => loadFromStorage<AppUser>(USERS_KEY, []));

  useEffect(() => {
    localStorage.setItem(CLEVELS_KEY, JSON.stringify(cLevels));
  }, [cLevels]);

  useEffect(() => {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  }, [users]);

  const addCLevel = (c: Omit<CLevel, "id">) => {
    setCLevels((prev) => [...prev, { ...c, id: crypto.randomUUID() }]);
  };

  const updateCLevel = (id: string, partial: Partial<CLevel>) => {
    setCLevels((prev) => prev.map((c) => (c.id === id ? { ...c, ...partial } : c)));
  };

  const toggleCLevel = (id: string) => {
    setCLevels((prev) => prev.map((c) => (c.id === id ? { ...c, ativo: !c.ativo } : c)));
  };

  const addUser = (u: Omit<AppUser, "id">) => {
    setUsers((prev) => [...prev, { ...u, id: crypto.randomUUID() }]);
  };

  const updateUser = (id: string, partial: Partial<AppUser>) => {
    setUsers((prev) => prev.map((u) => (u.id === id ? { ...u, ...partial } : u)));
  };

  const toggleUser = (id: string) => {
    setUsers((prev) =>
      prev.map((u) =>
        u.id === id ? { ...u, status: u.status === "ativo" ? "inativo" : "ativo" } : u
      )
    );
  };

  return (
    <SettingsContext.Provider value={{ cLevels, addCLevel, updateCLevel, toggleCLevel, users, addUser, updateUser, toggleUser }}>
      {children}
    </SettingsContext.Provider>
  );
}

export const useSettings = () => useContext(SettingsContext);
