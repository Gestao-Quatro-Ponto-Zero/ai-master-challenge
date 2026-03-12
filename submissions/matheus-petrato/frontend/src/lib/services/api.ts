// Re-export constants and types
export const API_BASE_URL = 'http://localhost:8080/api';

// Types
export interface User {
    id: string;
    email: string;
    name: string;
    role?: 'seller' | 'manager';
    region?: string;
    team_id?: string;
    manager_id?: string;
}

export interface AuthResponse {
    token: string;
    user: User;
}

export interface DataSource {
    id: string;
    name: string;
    type: string;
    config: string;
    is_active: boolean;
}

export interface Deal {
    id: string;
    name: string;
    score: number;
    stage?: string;
    days?: number;
    value?: number | string;
    trend?: number | string;
    status?: string;
    action?: string;
    owner?: string;
    factors?: Array<{ factor: string; impact: number; sentiment: string; detail?: string }>;
    next_actions?: string[];
}

// Stores (Svelte 5 runed store approach)
export function getStoredToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('g4_compass_token');
}

export function setStoredToken(token: string) {
    if (typeof window !== 'undefined') {
        localStorage.setItem('g4_compass_token', token);
    }
}

export function getStoredUser(): User | null {
    if (typeof window === 'undefined') return null;
    const user = localStorage.getItem('g4_compass_user');
    return user ? JSON.parse(user) : null;
}

export function setStoredUser(user: User) {
    if (typeof window !== 'undefined') {
        localStorage.setItem('g4_compass_user', JSON.stringify(user));
        if (user?.role) {
            localStorage.setItem('g4_compass_role', user.role);
        }
    }
}

export function clearStoredAuth() {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('g4_compass_token');
        localStorage.removeItem('g4_compass_user');
        localStorage.removeItem('g4_compass_role');
    }
}

// Authenticated Fetch Wrapper
async function apiFetch(endpoint: string, options: RequestInit = {}) {
    const token = getStoredToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        clearStoredAuth();
        window.location.href = '/login';
        throw new Error('Sessão expirada');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Erro desconhecido' }));
        throw new Error(error.message || 'Erro na requisição');
    }

    return response.json();
}

/**
 * Normaliza objetos vindo do Go (PascalCase) para camelCase/snake_case
 */
const mapDataSource = (ds: any): DataSource => ({
    id: ds.ID || ds.id,
    name: ds.Name || ds.name,
    type: ds.Type || ds.type,
    config: ds.Config || ds.config,
    is_active: ds.IsActive !== undefined ? ds.IsActive : (ds.is_active || false)
});

const mapUser = (u: any): User => ({
    id: u.ID || u.id,
    email: u.Email || u.email,
    name: u.Name || u.name,
    role: u.Role || u.role,
    region: u.Region || u.region,
    team_id: u.TeamID || u.team_id,
    manager_id: u.ManagerID || u.manager_id
});

export const api = {
    auth: {
        login: async (credentials: any) => {
            const res = await apiFetch('/auth/login', {
                method: 'POST',
                body: JSON.stringify(credentials)
            });
            return {
                token: res.token || res.Token,
                user: mapUser(res.user || res.User || res)
            };
        },
        register: async (data: any) => {
            const res = await apiFetch('/auth/register', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            return {
                token: res.token || res.Token,
                user: mapUser(res.user || res.User || res)
            };
        }
    },
    datasources: {
        list: async () => {
            const list = await apiFetch('/datasources');
            return Array.isArray(list) ? list.map(mapDataSource) : [];
        },
        create: async (data: Partial<DataSource>) => {
            const res = await apiFetch('/datasources', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            return mapDataSource(res);
        },
        update: async (id: string, data: Partial<DataSource>) => {
            const res = await apiFetch(`/datasources/${id}`, {
                method: 'PATCH',
                body: JSON.stringify(data)
            });
            return mapDataSource(res);
        },
        scan: async (id: string) => {
            const res = await apiFetch(`/datasources/${id}/scan`, {
                method: 'POST'
            });
            const draftRaw = res.draft || res.Draft || {};
            return {
                raw: res.raw || res.Raw || [],
                draft: {
                    tables: draftRaw.tables || draftRaw.Tables || {},
                    columns: draftRaw.columns || draftRaw.Columns || {}
                }
            };
        }
    },
    briefing: {
        get: () => apiFetch('/briefing')
    },
    deals: {
        list: (params: Record<string, string | number | undefined> = {}) => {
            const query = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    query.set(key, String(value));
                }
            });
            const suffix = query.toString() ? `?${query.toString()}` : '';
            return apiFetch(`/deals${suffix}`);
        },
        get: (id: string) => apiFetch(`/deals/${id}`)
    },
    alerts: {
        list: () => apiFetch('/alerts')
    },
    stats: {
        team: () => apiFetch('/stats/team')
    },
    imports: {
        list: () => apiFetch('/imports'),
        upload: async (file: File) => {
            const token = getStoredToken();
            const form = new FormData();
            form.append('file', file);
            const response = await fetch(`${API_BASE_URL}/imports`, {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {},
                body: form
            });
            if (response.status === 401) {
                clearStoredAuth();
                window.location.href = '/login';
                throw new Error('Sessão expirada');
            }
            if (!response.ok) {
                const error = await response.json().catch(() => ({ message: 'Erro desconhecido' }));
                throw new Error(error.message || 'Erro na requisição');
            }
            return response.json();
        },
        reprocess: (id: string) => apiFetch(`/imports/${id}/reprocess`, { method: 'POST' }),
        remove: (id: string) => apiFetch(`/imports/${id}`, { method: 'DELETE' })
    },
    chat: {
        history: (sessionId?: string) => {
            const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
            return apiFetch(`/chat/history${suffix}`);
        }
    }
};
