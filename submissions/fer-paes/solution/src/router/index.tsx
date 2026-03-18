import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import { AuthGuard } from '../components/AuthGuard';
import { PermissionGuard } from '../components/PermissionGuard';
import { AccessDenied } from '../components/AccessDenied';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Roles from '../pages/Roles';
import Users from '../pages/Users';
import Profile from '../pages/Profile';
import Audit from '../pages/Audit';
import Tickets from '../pages/Tickets';
import TicketDetail from '../pages/TicketDetail';
import Customers from '../pages/Customers';
import CustomerDetail from '../pages/CustomerDetail';
import Automations from '../pages/Automations';
import Macros from '../pages/Macros';
import Agents from '../pages/Agents';
import Knowledge  from '../pages/Knowledge';
import Operators  from '../pages/Operators';
import Queues              from '../pages/Queues';
import SupervisorDashboard from '../pages/SupervisorDashboard';
import OperatorMetrics     from '../pages/OperatorMetrics';
import OperatorWorkspace   from '../pages/OperatorWorkspace';
import LLMModels           from '../pages/LLMModels';
import LLMRequestsLog      from '../pages/LLMRequestsLog';
import TokenUsage          from '../pages/TokenUsage';
import LLMCosts            from '../pages/LLMCosts';
import LLMRouterDebug      from '../pages/LLMRouterDebug';
import LLMPolicies         from '../pages/LLMPolicies';
import LLMBudgets          from '../pages/LLMBudgets';
import AIUsageDashboard    from '../pages/AIUsageDashboard';
import CustomerAnalytics   from '../pages/CustomerAnalytics';
import Events              from '../pages/Events';
import CustomerSegments    from '../pages/CustomerSegments';
import Campaigns           from '../pages/Campaigns';
import CampaignScheduler   from '../pages/CampaignScheduler';
import CampaignDeliveries  from '../pages/CampaignDeliveries';
import CampaignAnalytics   from '../pages/CampaignAnalytics';
import CsvImport           from '../pages/CsvImport';
import Integrations        from '../pages/Integrations';
import Developers          from '../pages/Developers';
import NotFound            from '../pages/NotFound';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <MainLayout />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'roles',
        element: (
          <PermissionGuard permission="roles.manage" fallback={<AccessDenied />}>
            <Roles />
          </PermissionGuard>
        ),
      },
      {
        path: 'users',
        element: (
          <PermissionGuard permission="users.manage" fallback={<AccessDenied />}>
            <Users />
          </PermissionGuard>
        ),
      },
      {
        path: 'profile',
        element: <Profile />,
      },
      {
        path: 'audit',
        element: (
          <PermissionGuard permission="roles.manage" fallback={<AccessDenied />}>
            <Audit />
          </PermissionGuard>
        ),
      },
      {
        path: 'tickets',
        element: (
          <PermissionGuard permission="tickets.view" fallback={<AccessDenied />}>
            <Tickets />
          </PermissionGuard>
        ),
      },
      {
        path: 'tickets/:id',
        element: (
          <PermissionGuard permission="tickets.view" fallback={<AccessDenied />}>
            <TicketDetail />
          </PermissionGuard>
        ),
      },
      {
        path: 'customers',
        element: <Customers />,
      },
      {
        path: 'customers/:id',
        element: <CustomerDetail />,
      },
      {
        path: 'automations',
        element: (
          <PermissionGuard permission="roles.manage" fallback={<AccessDenied />}>
            <Automations />
          </PermissionGuard>
        ),
      },
      {
        path: 'macros',
        element: (
          <PermissionGuard permission="roles.manage" fallback={<AccessDenied />}>
            <Macros />
          </PermissionGuard>
        ),
      },
      {
        path: 'agents',
        element: (
          <PermissionGuard permission="agents.view" fallback={<AccessDenied />}>
            <Agents />
          </PermissionGuard>
        ),
      },
      {
        path: 'knowledge',
        element: (
          <PermissionGuard permission="knowledge.view" fallback={<AccessDenied />}>
            <Knowledge />
          </PermissionGuard>
        ),
      },
      {
        path: 'operators',
        element: (
          <PermissionGuard permission="operators.manage" fallback={<AccessDenied />}>
            <Operators />
          </PermissionGuard>
        ),
      },
      {
        path: 'queues',
        element: (
          <PermissionGuard permission="queues.manage" fallback={<AccessDenied />}>
            <Queues />
          </PermissionGuard>
        ),
      },
      {
        path: 'supervisor',
        element: (
          <PermissionGuard permission="operations.monitor" fallback={<AccessDenied />}>
            <SupervisorDashboard />
          </PermissionGuard>
        ),
      },
      {
        path: 'metrics',
        element: (
          <PermissionGuard permission="metrics.view" fallback={<AccessDenied />}>
            <OperatorMetrics />
          </PermissionGuard>
        ),
      },
      {
        path: 'workspace',
        element: (
          <PermissionGuard permission="tickets.handle" fallback={<AccessDenied />}>
            <OperatorWorkspace />
          </PermissionGuard>
        ),
      },
      {
        path: 'llm-models',
        element: (
          <PermissionGuard permission="llm_models.manage" fallback={<AccessDenied />}>
            <LLMModels />
          </PermissionGuard>
        ),
      },
      {
        path: 'llm-logs',
        element: (
          <PermissionGuard permission="llm_logs.view" fallback={<AccessDenied />}>
            <LLMRequestsLog />
          </PermissionGuard>
        ),
      },
      {
        path: 'token-usage',
        element: (
          <PermissionGuard permission="llm_usage.view" fallback={<AccessDenied />}>
            <TokenUsage />
          </PermissionGuard>
        ),
      },
      {
        path: 'llm-costs',
        element: (
          <PermissionGuard permission="llm_costs.view" fallback={<AccessDenied />}>
            <LLMCosts />
          </PermissionGuard>
        ),
      },
      {
        path: 'llm-router',
        element: (
          <PermissionGuard permission="system.internal" fallback={<AccessDenied />}>
            <LLMRouterDebug />
          </PermissionGuard>
        ),
      },
      {
        path: 'llm-policies',
        element: (
          <PermissionGuard permission="llm_policies.manage" fallback={<AccessDenied />}>
            <LLMPolicies />
          </PermissionGuard>
        ),
      },
      {
        path: 'llm-budgets',
        element: (
          <PermissionGuard permission="llm_budget.manage" fallback={<AccessDenied />}>
            <LLMBudgets />
          </PermissionGuard>
        ),
      },
      {
        path: 'ai-usage',
        element: (
          <PermissionGuard permission="ai_usage.view" fallback={<AccessDenied />}>
            <AIUsageDashboard />
          </PermissionGuard>
        ),
      },
      {
        path: 'customer-analytics',
        element: (
          <PermissionGuard permission="analytics.view" fallback={<AccessDenied />}>
            <CustomerAnalytics />
          </PermissionGuard>
        ),
      },
      {
        path: 'events',
        element: (
          <PermissionGuard permission="events.view" fallback={<AccessDenied />}>
            <Events />
          </PermissionGuard>
        ),
      },
      {
        path: 'segments',
        element: (
          <PermissionGuard permission="segments.manage" fallback={<AccessDenied />}>
            <CustomerSegments />
          </PermissionGuard>
        ),
      },
      {
        path: 'campaigns',
        element: (
          <PermissionGuard permission="campaigns.manage" fallback={<AccessDenied />}>
            <Campaigns />
          </PermissionGuard>
        ),
      },
      {
        path: 'campaign-scheduler',
        element: (
          <PermissionGuard permission="campaign_scheduler.manage" fallback={<AccessDenied />}>
            <CampaignScheduler />
          </PermissionGuard>
        ),
      },
      {
        path: 'campaign-deliveries',
        element: (
          <PermissionGuard permission="campaigns.view" fallback={<AccessDenied />}>
            <CampaignDeliveries />
          </PermissionGuard>
        ),
      },
      {
        path: 'campaign-analytics',
        element: (
          <PermissionGuard permission="campaigns.analytics" fallback={<AccessDenied />}>
            <CampaignAnalytics />
          </PermissionGuard>
        ),
      },
      {
        path: 'import',
        element: (
          <PermissionGuard permission="roles.manage" fallback={<AccessDenied />}>
            <CsvImport />
          </PermissionGuard>
        ),
      },
      {
        path: 'integrations',
        element: (
          <PermissionGuard permission="integrations.manage" fallback={<AccessDenied />}>
            <Integrations />
          </PermissionGuard>
        ),
      },
      {
        path: 'developers',
        element: (
          <PermissionGuard permission="integrations.manage" fallback={<AccessDenied />}>
            <Developers />
          </PermissionGuard>
        ),
      },
    ],
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);
