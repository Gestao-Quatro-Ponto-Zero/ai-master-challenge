export function startTimer() {
  const startedAt = Date.now();
  return {
    done(label: string) {
      const elapsedMs = Date.now() - startedAt;
      console.info(`[metric] ${label}=${elapsedMs}ms`);
      return elapsedMs;
    },
  };
}
