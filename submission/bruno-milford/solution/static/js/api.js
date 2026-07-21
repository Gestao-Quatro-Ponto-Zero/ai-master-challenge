window.Raven = window.Raven || {};

window.Raven.api = {
  async get(path, filters = {}) {
    const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value !== "" && value !== null && value !== undefined));
    const url = query.toString() ? `${path}?${query}` : path;
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    const type = response.headers.get("content-type") || "";
    const payload = type.includes("application/json") ? await response.json() : null;
    if (!response.ok || (payload && payload.success === false)) {
      throw new Error(payload?.error || "Nao foi possivel carregar os dados.");
    }
    return payload ? payload.data : response;
  }
};
