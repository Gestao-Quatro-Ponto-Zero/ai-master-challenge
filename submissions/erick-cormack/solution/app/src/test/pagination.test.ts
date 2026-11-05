import { describe, expect, it } from "vitest";
import { paginate } from "@/lib/pagination";

describe("paginação do Meu pipeline", () => {
  it("divide as oportunidades em páginas de 25 sem perder ou repetir registros", () => {
    const deals = Array.from({ length: 58 }, (_, i) => i);
    const first = paginate(deals, 1);
    const second = paginate(deals, 2);
    const last = paginate(deals, 3);
    expect(first.items).toHaveLength(25);
    expect(second.items).toHaveLength(25);
    expect(last.items).toHaveLength(8);
    expect(second.start).toBe(25);
    expect(last.totalPages).toBe(3);
    expect([...first.items, ...second.items, ...last.items]).toEqual(deals);
    expect(paginate(deals.slice(0, 5), 3).page).toBe(1);
  });
});