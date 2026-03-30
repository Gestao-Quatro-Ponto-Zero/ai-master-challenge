const API_BASE_URL = "https://postoral-stan-salamandrine.ngrok-free.dev";

const defaultHeaders: Record<string, string> = {
  "Content-Type": "application/json",
  "ngrok-skip-browser-warning": "true",
};

export async function fetchKPIs() {
  const res = await fetch(`${API_BASE_URL}/kpis`, { headers: defaultHeaders });
  if (!res.ok) throw new Error("Falha ao carregar KPIs");
  return res.json();
}

export async function fetchDashboardValidation() {
  const res = await fetch(`${API_BASE_URL}/dashboard-validation`, { headers: defaultHeaders });
  if (!res.ok) throw new Error("Falha ao carregar dashboard");
  return res.json();
}

export async function fetchChurnRisk() {
  const res = await fetch(`${API_BASE_URL}/churn-risk`, { headers: defaultHeaders });
  if (!res.ok) throw new Error("Falha ao carregar dados de risco de churn");
  return res.json();
}

export async function fetchInsights() {
  const res = await fetch(`${API_BASE_URL}/insights`, { headers: defaultHeaders });
  if (!res.ok) throw new Error("Falha ao carregar insights");
  return res.json();
}

export async function fetchRecommendations() {
  const res = await fetch(`${API_BASE_URL}/recommendations`, { headers: defaultHeaders });
  if (!res.ok) throw new Error("Falha ao carregar recomendações");
  return res.json();
}

export async function fetchOpenRecommendations() {
  const res = await fetch(`${API_BASE_URL}/whatsapp/open-recommendations`, { headers: defaultHeaders });
  if (!res.ok) throw new Error("Falha ao carregar recomendações abertas");
  return res.json();
}

export async function fetchKanbanProjects() {
  const res = await fetch(`${API_BASE_URL}/kanban/projects`, { headers: defaultHeaders });
  if (!res.ok) throw new Error("Falha ao carregar projetos Kanban");
  return res.json();
}

export async function approveRecommendation(recommendationId: string) {
  const res = await fetch(`${API_BASE_URL}/kanban/projects/approve`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ recommendation_id: recommendationId }),
  });
  if (!res.ok) throw new Error("Falha ao aprovar recomendação");
  return res.json();
}

export async function moveKanbanProject(projectId: string, newStage: string) {
  const res = await fetch(`${API_BASE_URL}/kanban/projects/${projectId}/move`, {
    method: "PATCH",
    headers: defaultHeaders,
    body: JSON.stringify({ new_stage: newStage }),
  });
  if (!res.ok) throw new Error("Falha ao mover projeto");
  return res.json();
}

export async function deleteKanbanProject(projectId: string) {
  const res = await fetch(`${API_BASE_URL}/kanban/projects/${projectId}`, {
    method: "DELETE",
    headers: defaultHeaders,
  });
  if (!res.ok) throw new Error("Falha ao excluir projeto");
  return res.json();
}

export async function askAI(question: string) {
  const res = await fetch(`${API_BASE_URL}/ask-ai`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error("Falha na consulta IA");
  return res.json();
}

export async function notifyWhatsApp(recommendationId: string, target: string) {
  const res = await fetch(`${API_BASE_URL}/whatsapp/notify`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ recommendation_id: recommendationId, target }),
  });
  if (!res.ok) throw new Error("Falha ao notificar WhatsApp");
  return res.json();
}

export async function webhookWhatsApp(action: string, recommendationId: string, notes?: string) {
  const res = await fetch(`${API_BASE_URL}/whatsapp/webhook`, {
    method: "POST",
    headers: defaultHeaders,
    body: JSON.stringify({ action, recommendation_id: recommendationId, notes }),
  });
  if (!res.ok) throw new Error("Falha no webhook WhatsApp");
  return res.json();
}
