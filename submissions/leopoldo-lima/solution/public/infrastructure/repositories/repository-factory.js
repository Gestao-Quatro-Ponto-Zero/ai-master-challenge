import { assertOpportunityRepository } from "../../application/contracts/opportunity-repository.js";
import { ApiOpportunityRepository } from "./api-opportunity-repository.js";
import { MockOpportunityRepository } from "./mock-opportunity-repository.js";

/** Repositório principal = API (dataset real). Modo mock só para desenvolvimento explícito (CRP-UX-01). */
export function createOpportunityRepository() {
  const mode = String(window.LEAD_SCORER_REPOSITORY_MODE || "api").trim().toLowerCase();
  const repository = mode === "mock" ? new MockOpportunityRepository() : new ApiOpportunityRepository();
  assertOpportunityRepository(repository);
  return repository;
}
