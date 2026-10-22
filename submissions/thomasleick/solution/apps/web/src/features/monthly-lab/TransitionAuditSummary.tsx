import { useEffect, useState } from 'react'
import { getTransitionAudit } from '../../lib/api'

export function TransitionAuditSummary() {
  const [audit, setAudit] = useState<Record<string, any> | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { getTransitionAudit().then(setAudit).catch((issue: Error) => setError(issue.message)) }, [])
  if (error) return <p className="table-warning" role="alert">Transition flag audit could not load: {error}</p>
  if (!audit) return <p className="small-note" role="status">Loading transition flag audit…</p>
  const flags = audit.explicit_flags
  const classifications = audit.classification_counts
  if (!flags || !classifications) return <p className="table-warning" role="status">Transition flag evidence is unavailable in this API response.</p>
  return <section className="panel light-panel transition-audit" aria-labelledby="transition-audit-heading" data-testid="transition-audit-summary">
    <div className="panel-head"><div><span className="panel-index">SOURCE FLAGS ≠ MIGRATION LEDGER</span><h3 id="transition-audit-heading">Upgrade and downgrade signals have row-level evidence only</h3><p>The CSV reports mid-cycle flags, but does not link each flag to a dated from-plan / to-plan pair.</p></div><span className="evidence-pill alert">NOT CONFIRMED</span></div>
    <div className="transition-audit-stats"><div><b>{flags.upgrade_flag_rows}</b><span>subscription rows with upgrade_flag</span></div><div><b>{flags.downgrade_flag_rows}</b><span>subscription rows with downgrade_flag</span></div><div><b>{flags.rows_with_both_flags}</b><span>rows carrying both flags</span></div><div><b>{flags.flagged_rows_with_null_end_date.upgrade_rows} / {flags.flagged_rows_with_null_end_date.downgrade_rows}</b><span>flagged rows with null end date · upgrade / downgrade</span></div><div><b>{classifications.confirmed} / {classifications.inferred} / {classifications.possible}</b><span>confirmed / inferred / candidate interval pairs</span></div></div>
    <p className="table-warning">The 52 possible upgrade pairs and 51 possible downgrade pairs within 30 days use the unverified Basic &lt; Pro &lt; Enterprise name-order assumption. Row flags do not validate that hierarchy or identify transition direction for a specific pair. Recorded MRR amounts are not a reconciled before/after revenue measure.</p>
  </section>
}
