import { loadAndScoreDeals } from '@/lib/lead-scorer';
import LeadScorerDashboard from './dashboard';

export const dynamic = 'force-dynamic';

export default function LeadScorerPage() {
  const { deals, summary } = loadAndScoreDeals();
  return <LeadScorerDashboard deals={deals} summary={summary} />;
}
