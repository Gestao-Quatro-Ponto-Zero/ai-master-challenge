import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.dirname(fileURLToPath(import.meta.url));

// Keep the delivered app independent of any parent workspace or lockfile.
export default {
  turbopack: { root: projectRoot },
  outputFileTracingRoot: projectRoot,
};
