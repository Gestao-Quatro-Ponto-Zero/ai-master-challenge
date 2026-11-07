import { eventNames } from "./activity.mjs";

// Public compatibility contract: changing these keys would orphan existing data.
export const WORKSPACE_KEY = "g4-sales-workspace-v2";
export const PREFERENCES_KEY = "g4-ui-preferences";

/**
 * Synchronous adapter for the demonstration's browser storage.
 * Receives Storage explicitly so domain tests do not need window/localStorage.
 * A shared server adapter will also need async save handling in the workspace hook.
 * @param {Pick<Storage, 'getItem'|'setItem'>} storage
 */
export function createLocalWorkspaceRepository(storage) {
  return {
    load() {
      const saved = JSON.parse(storage.getItem(WORKSPACE_KEY) || "null");
      if (!saved) return null;
      if (!Array.isArray(saved.events)) throw Error("Invalid workspace events");
      return {
        ...saved,
        events: saved.events.filter(
          (e) =>
            e &&
            typeof e.opportunityId === "string" &&
            typeof e.at === "string" &&
            Object.hasOwn(eventNames, e.type),
        ),
        plans:
          saved.plans && typeof saved.plans === "object" ? saved.plans : {},
      };
    },
    /** @param {import('./contracts.mjs').WorkspaceSnapshot} snapshot */
    save(snapshot) {
      storage.setItem(
        WORKSPACE_KEY,
        JSON.stringify({ ...snapshot, version: 2 }),
      );
    },
    loadPreferences() {
      return JSON.parse(storage.getItem(PREFERENCES_KEY) || "{}");
    },
    savePreferences(preferences) {
      storage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
    },
  };
}
