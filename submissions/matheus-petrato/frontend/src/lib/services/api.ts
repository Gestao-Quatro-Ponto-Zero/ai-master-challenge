// Re-export constants and types
export const API_BASE_URL = 'http://localhost:8080';

// Types
export interface User {
    id: string;
    email: string;
    name: string;
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

// Stores (Svelte 5 runed store approach)
export function getStoredToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('datapus_token');
}

export function setStoredToken(token: string) {
    if (typeof window !== 'undefined') {
        localStorage.setItem('datapus_token', token);
    }
}

export function getStoredUser(): User | null {
    if (typeof window === 'undefined') return null;
    const user = localStorage.getItem('datapus_user');
    return user ? JSON.parse(user) : null;
}

export function setStoredUser(user: User) {
    if (typeof window !== 'undefined') {
        localStorage.setItem('datapus_user', JSON.stringify(user));
    }
}

export function clearStoredAuth() {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('datapus_token');
        localStorage.removeItem('datapus_user');
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
    name: u.Name || u.name
});

export const api = {
    auth: {
        login: async (credentials: any) => {
            const res = await apiFetch('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify(credentials)
            });
            return {
                token: res.token || res.Token,
                user: mapUser(res.user || res.User || res)
            };
        },
        register: async (data: any) => {
            const res = await apiFetch('/api/auth/register', {
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
            const list = await apiFetch('/api/v1/datasources');
            return Array.isArray(list) ? list.map(mapDataSource) : [];
        },
        create: async (data: Partial<DataSource>) => {
            const res = await apiFetch('/api/v1/datasources', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            return mapDataSource(res);
        },
        update: async (id: string, data: Partial<DataSource>) => {
            const res = await apiFetch(`/api/v1/datasources/${id}`, {
                method: 'PATCH',
                body: JSON.stringify(data)
            });
            return mapDataSource(res);
        },
        scan: async (id: string) => {
            const res = await apiFetch(`/api/v1/datasources/${id}/scan`, {
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
    chat: {
        history: () => apiFetch('/api/v1/chat/history') 
    }
};
