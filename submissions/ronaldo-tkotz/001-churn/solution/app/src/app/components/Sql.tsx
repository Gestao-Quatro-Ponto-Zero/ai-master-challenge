/** The exact query behind a claim. Mono, quiet, inspectable — wraps, never scrolls sideways. */
export function Sql({ sql, rowCount }: { sql: string; rowCount?: number }) {
  return (
    <div className="rounded-md border border-edge bg-background/60">
      <div className="flex items-center justify-between border-b border-edge px-2.5 py-1.5">
        <span className="text-[10px] font-medium uppercase tracking-wider text-faint">SQL</span>
        {typeof rowCount === "number" && (
          <span className="font-mono text-[10px] text-faint">
            {rowCount.toLocaleString("en-US")} row{rowCount === 1 ? "" : "s"}
          </span>
        )}
      </div>
      <pre className="whitespace-pre-wrap break-words px-2.5 py-2 text-[11.5px] leading-relaxed">
        <code className="font-mono text-muted">{sql.trim()}</code>
      </pre>
    </div>
  );
}
