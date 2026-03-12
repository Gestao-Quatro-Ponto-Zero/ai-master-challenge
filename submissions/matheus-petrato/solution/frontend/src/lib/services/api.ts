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
            // Support page instead of offset: page=2 with limit=20 -> offset=20
            const page = params.page !== undefined ? Number(params.page) : 1;
            const limit = params.limit !== undefined ? Number(params.limit) : 20;
            if (!query.has('offset') && page > 1) {
                query.set('offset', String((page - 1) * limit));
            }
            if (!query.has('limit')) {
                query.set('limit', String(limit));
            }
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
        upload: async (file: File, type: string) => {
            const token = getStoredToken();
            const form = new FormData();
            form.append('file', file);
            form.append('type', type);
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
