import { useState, useMemo, Fragment } from 'react';
import { ChevronDown, ChevronUp, ChevronRight, AlertTriangle, Info } from 'lucide-react';

const ITEMS_PER_PAGE = 25;

function ScoreBreakdown({ deal }) {
    return (
        <div className="breakdown-content">
            {!deal.hasAccount && (
                <div className="no-account-warning">
                    <AlertTriangle size={14} />
                    No account linked — scoring based on Agent + Product + Stage
                </div>
            )}
            {deal.breakdown.map((factor, idx) => {
                const barColor =
                    factor.score >= 70
                        ? 'var(--hot)'
                        : factor.score >= 50
                            ? 'var(--warm)'
                            : factor.score >= 30
                                ? 'var(--cool)'
                                : 'var(--cold)';

                if (factor.weight === 0) return null;

                return (
                    <div className="breakdown-factor" key={idx}>
                        <div className="breakdown-factor-header">
                            <span className="breakdown-factor-name">{factor.factor}</span>
                            <span
                                className="breakdown-factor-score"
                                style={{ color: barColor }}
                            >
                                {factor.contribution}pts
                                <span className="text-muted" style={{ fontSize: '0.7rem', fontWeight: 400 }}>
                                    {' '}({factor.weight}%)
                                </span>
                            </span>
                        </div>
                        <div className="breakdown-bar">
                            <div
                                className="breakdown-bar-fill"
                                style={{
                                    width: `${factor.score}%`,
                                    background: barColor,
                                }}
                            />
                        </div>
                        <span className="breakdown-factor-detail">{factor.detail}</span>
                    </div>
                );
            })}
            <div className="breakdown-summary">
                <div>
                    <div className="breakdown-summary-label">Win Probability</div>
                    <div className="breakdown-summary-value">{deal.winProbability}%</div>
                </div>
                <div style={{ marginLeft: 8 }}>
                    <div className="breakdown-summary-label">
                        × ${deal.productValue.toLocaleString()} product value
                    </div>
                </div>
                <div style={{ marginLeft: 'auto' }}>
                    <div className="breakdown-summary-label">Priority Score</div>
                    <div className="breakdown-summary-value" style={{ fontSize: '1.3rem' }}>
                        {deal.priorityScore}
                    </div>
                </div>
                <div>
                    <div className="breakdown-summary-label">Expected Value</div>
                    <div className="breakdown-summary-value text-green">
                        ${deal.expectedValue.toLocaleString()}
                    </div>
                </div>
            </div>
        </div>
    );
}

export function PipelineTable({ deals }) {
    const [sortField, setSortField] = useState('priorityScore');
    const [sortDir, setSortDir] = useState('desc');
    const [expandedId, setExpandedId] = useState(null);
    const [page, setPage] = useState(0);

    // Sort  
    const sortedDeals = useMemo(() => {
        const sorted = [...deals].sort((a, b) => {
            let va = a[sortField];
            let vb = b[sortField];
            if (va == null) va = '';
            if (vb == null) vb = '';
            if (typeof va === 'string') {
                return sortDir === 'asc'
                    ? va.localeCompare(vb)
                    : vb.localeCompare(va);
            }
            return sortDir === 'asc' ? va - vb : vb - va;
        });
        return sorted;
    }, [deals, sortField, sortDir]);

    // Paginate
    const totalPages = Math.ceil(sortedDeals.length / ITEMS_PER_PAGE);
    const pagedDeals = sortedDeals.slice(
        page * ITEMS_PER_PAGE,
        (page + 1) * ITEMS_PER_PAGE
    );

    // Reset page when deals change
    useMemo(() => setPage(0), [deals]);

    const handleSort = (field) => {
        if (sortField === field) {
            setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
        } else {
            setSortField(field);
            setSortDir('desc');
        }
    };

    const SortIcon = ({ field }) => {
        if (sortField !== field)
            return <ChevronRight size={12} style={{ opacity: 0.3 }} />;
        return sortDir === 'asc' ? (
            <ChevronUp size={12} />
        ) : (
            <ChevronDown size={12} />
        );
    };

    if (!deals.length) {
        return (
            <div className="card">
                <div className="empty-state">
                    <Info size={32} />
                    <p>No deals match your filters</p>
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="pipeline-table-wrapper">
                <table className="pipeline-table">
                    <thead>
                        <tr>
                            <th
                                className={sortField === 'priorityScore' ? 'sorted' : ''}
                                onClick={() => handleSort('priorityScore')}
                            >
                                Score <SortIcon field="priorityScore" />
                            </th>
                            <th
                                className={sortField === 'account' ? 'sorted' : ''}
                                onClick={() => handleSort('account')}
                            >
                                Account <SortIcon field="account" />
                            </th>
                            <th
                                className={sortField === 'product' ? 'sorted' : ''}
                                onClick={() => handleSort('product')}
                            >
                                Product <SortIcon field="product" />
                            </th>
                            <th
                                className={sortField === 'sales_agent' ? 'sorted' : ''}
                                onClick={() => handleSort('sales_agent')}
                            >
                                Agent <SortIcon field="sales_agent" />
                            </th>
                            <th
                                className={sortField === 'deal_stage' ? 'sorted' : ''}
                                onClick={() => handleSort('deal_stage')}
                            >
                                Stage <SortIcon field="deal_stage" />
                            </th>
                            <th
                                className={sortField === 'daysInPipeline' ? 'sorted' : ''}
                                onClick={() => handleSort('daysInPipeline')}
                            >
                                Days <SortIcon field="daysInPipeline" />
                            </th>
                            <th
                                className={sortField === 'productValue' ? 'sorted' : ''}
                                onClick={() => handleSort('productValue')}
                            >
                                Value <SortIcon field="productValue" />
                            </th>
                            <th
                                className={sortField === 'expectedValue' ? 'sorted' : ''}
                                onClick={() => handleSort('expectedValue')}
                            >
                                EV <SortIcon field="expectedValue" />
                            </th>
                            <th>Why?</th>
                        </tr>
                    </thead>
                    <tbody>
                        {pagedDeals.map((deal) => (
                            <Fragment key={deal.opportunity_id}>
                                <tr
                                    className={
                                        expandedId === deal.opportunity_id ? 'expanded-parent' : ''
                                    }
                                >
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center' }}>
                                            <span
                                                className={`score-badge ${deal.label.toLowerCase()}`}
                                            >
                                                {deal.priorityScore}
                                            </span>
                                            <span
                                                className="score-label"
                                                style={{ color: deal.color }}
                                            >
                                                {deal.label}
                                            </span>
                                        </div>
                                    </td>
                                    <td>
                                        <span
                                            className="truncate"
                                            title={deal.account || 'No account'}
                                        >
                                            {deal.account || (
                                                <span className="text-muted">—</span>
                                            )}
                                        </span>
                                    </td>
                                    <td>{deal.product}</td>
                                    <td className="truncate" title={deal.sales_agent}>
                                        {deal.sales_agent}
                                    </td>
                                    <td>
                                        <span
                                            className={`stage-badge ${deal.deal_stage.toLowerCase()}`}
                                        >
                                            {deal.deal_stage}
                                        </span>
                                    </td>
                                    <td className="font-mono">
                                        {deal.daysInPipeline != null ? deal.daysInPipeline : '—'}
                                    </td>
                                    <td className="font-mono">
                                        ${deal.productValue.toLocaleString()}
                                    </td>
                                    <td className="font-mono text-green">
                                        ${deal.expectedValue.toLocaleString()}
                                    </td>
                                    <td>
                                        <button
                                            className={`expand-btn ${expandedId === deal.opportunity_id ? 'expanded' : ''
                                                }`}
                                            onClick={() =>
                                                setExpandedId(
                                                    expandedId === deal.opportunity_id
                                                        ? null
                                                        : deal.opportunity_id
                                                )
                                            }
                                        >
                                            {expandedId === deal.opportunity_id ? 'Hide' : 'Why?'}
                                        </button>
                                    </td>
                                </tr>
                                {expandedId === deal.opportunity_id && (
                                    <tr
                                        key={`${deal.opportunity_id}-breakdown`}
                                        className="breakdown-row"
                                    >
                                        <td colSpan={9}>
                                            <ScoreBreakdown deal={deal} />
                                        </td>
                                    </tr>
                                )}
                            </Fragment>
                        ))}
                    </tbody>
                </table>
            </div>
            {totalPages > 1 && (
                <div className="pagination">
                    <span>
                        Showing {page * ITEMS_PER_PAGE + 1}–
                        {Math.min((page + 1) * ITEMS_PER_PAGE, sortedDeals.length)} of{' '}
                        {sortedDeals.length} deals
                    </span>
                    <div className="pagination-controls">
                        <button
                            className="pagination-btn"
                            disabled={page === 0}
                            onClick={() => setPage(0)}
                        >
                            ««
                        </button>
                        <button
                            className="pagination-btn"
                            disabled={page === 0}
                            onClick={() => setPage(page - 1)}
                        >
                            «
                        </button>
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                            const start = Math.max(
                                0,
                                Math.min(page - 2, totalPages - 5)
                            );
                            const pageNum = start + i;
                            if (pageNum >= totalPages) return null;
                            return (
                                <button
                                    key={pageNum}
                                    className={`pagination-btn ${page === pageNum ? 'active' : ''}`}
                                    onClick={() => setPage(pageNum)}
                                >
                                    {pageNum + 1}
                                </button>
                            );
                        })}
                        <button
                            className="pagination-btn"
                            disabled={page === totalPages - 1}
                            onClick={() => setPage(page + 1)}
                        >
                            »
                        </button>
                        <button
                            className="pagination-btn"
                            disabled={page === totalPages - 1}
                            onClick={() => setPage(totalPages - 1)}
                        >
                            »»
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
