window.Raven = window.Raven || {};

window.Raven.format = {
  money(value) {
    return `$ ${Number(value || 0).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    })}`;
  },
  percent(value, digits = 1) {
    return `${Number(value || 0).toFixed(digits)}%`;
  },
  number(value) {
    return Number(value || 0).toLocaleString("en-US");
  },
  date(value) {
    if (!value) return "-";
    const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  },
  shortDate(value) {
    if (!value) return "-";
    const parsed = new Date(`${String(value).slice(0, 10)}T00:00:00`);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  },
  riskLabel(value) {
    return ({ critico: "Critico", alto: "Alto", medio: "Medio", baixo: "Baixo" }[value] || value || "-");
  }
};
