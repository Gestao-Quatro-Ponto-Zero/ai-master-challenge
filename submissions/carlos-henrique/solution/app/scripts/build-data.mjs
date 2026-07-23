import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export function resolveBuildPaths(moduleUrl = import.meta.url) {
  const scriptFile = fileURLToPath(moduleUrl);
  const appDir = path.resolve(path.dirname(scriptFile), "..");
  const solutionDir = path.resolve(appDir, "..");

  return {
    appDir,
    builderPath: path.resolve(solutionDir, "scripts", "build_dashboard_data.py"),
    solutionDir,
  };
}

export const buildPaths = resolveBuildPaths();

export function getPythonCandidates(
  platform = process.platform,
  solutionDir = buildPaths.solutionDir,
) {
  const isWindows = platform === "win32";
  const venvPython = path.resolve(
    solutionDir,
    ".venv",
    isWindows ? "Scripts" : "bin",
    isWindows ? "python.exe" : "python",
  );

  const commonCandidates = isWindows
    ? [
        { command: "py", args: ["-3"], label: "py -3" },
        { command: "python", args: [], label: "python" },
      ]
    : [
        { command: "python3", args: [], label: "python3" },
        { command: "python", args: [], label: "python" },
      ];

  return [
    { command: venvPython, args: [], label: "project virtual environment" },
    ...commonCandidates,
  ];
}

export function findPython(candidates, spawn = spawnSync) {
  for (const candidate of candidates) {
    const probe = spawn(candidate.command, [...candidate.args, "--version"], {
      shell: false,
      stdio: "ignore",
    });

    if (!probe.error && probe.status === 0) {
      return candidate;
    }
  }

  return null;
}

export function runBuildData({
  logger = console,
  paths = buildPaths,
  platform = process.platform,
  spawn = spawnSync,
} = {}) {
  if (!existsSync(paths.builderPath)) {
    logger.error(`[build:data] Builder not found: ${paths.builderPath}`);
    return 1;
  }

  const python = findPython(
    getPythonCandidates(platform, paths.solutionDir),
    spawn,
  );

  if (!python) {
    logger.error(
      "[build:data] Python 3 was not found. Create solution/.venv or install py -3/python on Windows, or python3/python on Linux and macOS, then install solution/requirements.txt.",
    );
    return 1;
  }

  logger.log(`[build:data] Python: ${python.label}`);
  const result = spawn(
    python.command,
    [...python.args, paths.builderPath],
    {
      cwd: paths.solutionDir,
      shell: false,
      stdio: "inherit",
    },
  );

  if (result.error) {
    logger.error(`[build:data] Failed to start the builder: ${result.error.message}`);
    return 1;
  }

  const exitCode = Number.isInteger(result.status) ? result.status : 1;
  if (exitCode !== 0) {
    logger.error(`[build:data] Builder failed with exit code ${exitCode}.`);
  }
  return exitCode;
}

const moduleFile = path.resolve(fileURLToPath(import.meta.url));
const entryFile = process.argv[1] ? path.resolve(process.argv[1]) : "";
const isMain =
  process.platform === "win32"
    ? moduleFile.toLowerCase() === entryFile.toLowerCase()
    : moduleFile === entryFile;

if (isMain) {
  process.exitCode = runBuildData();
}
