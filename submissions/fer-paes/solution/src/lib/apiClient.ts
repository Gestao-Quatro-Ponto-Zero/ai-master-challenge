import { supabase } from './supabaseClient';

export type ApiResponse<T> = { data: T; error: null } | { data: null; error: string };

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
  if (response.status === 401) {
    await supabase.auth.signOut();
    window.location.href = '/login';
    return { data: null, error: 'unauthorized' };
  }

  if (response.status === 403) {
    return { data: null, error: 'forbidden' };
  }

  if (!response.ok) {
    let message = 'Request failed';
    try {
      const body = await response.json();
      message = body?.error || body?.message || message;
    } catch {
      // ignore parse error
    }
    return { data: null, error: message };
  }

  try {
    const data = await response.json();
    return { data, error: null };
  } catch {
    return { data: null as unknown as T, error: null };
  }
}

export async function apiGet<T>(url: string): Promise<ApiResponse<T>> {
  const headers = await getAuthHeaders();
  const response = await fetch(url, { headers });
  return handleResponse<T>(response);
}

export async function apiPost<T>(url: string, body: unknown): Promise<ApiResponse<T>> {
  const headers = { ...(await getAuthHeaders()), 'Content-Type': 'application/json' };
  const response = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
  return handleResponse<T>(response);
}

export async function apiPatch<T>(url: string, body: unknown): Promise<ApiResponse<T>> {
  const headers = { ...(await getAuthHeaders()), 'Content-Type': 'application/json' };
  const response = await fetch(url, { method: 'PATCH', headers, body: JSON.stringify(body) });
  return handleResponse<T>(response);
}

export async function apiDelete<T>(url: string): Promise<ApiResponse<T>> {
  const headers = await getAuthHeaders();
  const response = await fetch(url, { method: 'DELETE', headers });
  return handleResponse<T>(response);
}
