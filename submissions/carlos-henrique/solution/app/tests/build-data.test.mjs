import path from "node:path";
import { describe, expect, it, vi } from "vitest";

import {
  buildPaths,
  getPythonCandidates,
  runBuildData,
} from "../scripts/build-data.mjs";

describe("cross-platform build:data wrapper", () => {
  it("resolves the builder, runs without a shell, succeeds, and propagates errors", () => {
    expect(buildPaths.builderPath).toBe(
      path.resolve(buildPaths.solutionDir, "scripts", "build_dashboard_data.py"),
    );
    expect(getPythonCandidates("win32", buildPaths.solutionDir).map(({ label }) => label)).toEqual([
      "project virtual environment",
      "py -3",
      "python",
    ]);
    expect(getPythonCandidates("linux", buildPaths.solutionDir).map(({ label }) => label)).toEqual([
      "project virtual environment",
      "python3",
      "python",
    ]);

    const successfulCalls = [];
    const successfulSpawn = vi.fn((command, args, options) => {
      successfulCalls.push({ command, args, options });
      return { error: undefined, status: 0 };
    });
    const logger = { error: vi.fn(), log: vi.fn() };

    expect(runBuildData({ logger, platform: "linux", spawn: successfulSpawn })).toBe(0);
    expect(successfulCalls).toHaveLength(2);
    expect(successfulCalls[0].args.at(-1)).toBe("--version");
    expect(successfulCalls[0].options.shell).toBe(false);
    expect(successfulCalls[1].args.at(-1)).toBe(buildPaths.builderPath);
    expect(successfulCalls[1].options).toMatchObject({
      cwd: buildPaths.solutionDir,
      shell: false,
      stdio: "inherit",
    });

    const failingSpawn = vi
      .fn()
      .mockReturnValueOnce({ error: undefined, status: 0 })
      .mockReturnValueOnce({ error: undefined, status: 9 });

    expect(runBuildData({ logger, platform: "linux", spawn: failingSpawn })).toBe(9);
    expect(logger.error).toHaveBeenCalledWith(
      "[build:data] Builder failed with exit code 9.",
    );
  });
});
