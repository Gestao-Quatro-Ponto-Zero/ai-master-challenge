import { STAGES } from "./workflow.mjs";
export const fmt = new Intl.NumberFormat("pt-BR"),
  usd = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
export const dateLabel = (v) =>
  new Date(v).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
export const initials = (n) =>
  (n || "?")
    .split(" ")
    .slice(0, 2)
    .map((s) => s[0])
    .join("");
export const matches = (d, q) =>
  `${d.account || ""} ${d.product} ${d.opportunity_id}`
    .toLowerCase()
    .includes(q.toLowerCase());
export const stageName = (id) => STAGES.find((s) => s.id === id)?.label;
export const sameDay = (a, b) =>
  new Date(a).toDateString() === new Date(b).toDateString();
