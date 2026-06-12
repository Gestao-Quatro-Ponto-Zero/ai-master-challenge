import express from 'express';
import cors from 'cors';
import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Database connection
const dbPath = path.join(__dirname, '../data/sales.db');
const db = new Database(dbPath, { readonly: true });

// API Endpoints

// Get all opportunities with scores
app.get('/opportunities', (req, res) => {
  try {
    const {
      sales_agent,
      deal_stage,
      account,
      product,
      min_score,
      sort_by = 'total_score',
      sort_dir = 'DESC',
      limit = 100,
      offset = 0
    } = req.query;

    let query = `
      SELECT 
        sp.opportunity_id,
        sp.sales_agent,
        sp.product,
        sp.account,
        sp.deal_stage,
        sp.engage_date,
        sp.close_date,
        sp.close_value,
        a.revenue,
        a.employees,
        a.sector,
        st.manager,
        st.regional_office,
        p.sales_price,
        ds.total_score,
        ds.stage_score,
        ds.account_score,
        ds.seller_score,
        ds.product_score,
        ds.time_score,
        ds.success_probability
      FROM sales_pipeline sp
      LEFT JOIN accounts a ON sp.account = a.account
      LEFT JOIN sales_teams st ON sp.sales_agent = st.sales_agent
      LEFT JOIN products p ON sp.product = p.product
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE 1=1
    `;

    const params = [];

    if (sales_agent) {
      query += ' AND sp.sales_agent = ?';
      params.push(sales_agent);
    }
    if (deal_stage) {
      query += ' AND sp.deal_stage = ?';
      params.push(deal_stage);
    }
    if (account) {
      query += ' AND sp.account LIKE ?';
      params.push(`%${account}%`);
    }
    if (product) {
      query += ' AND sp.product = ?';
      params.push(product);
    }
    if (min_score) {
      query += ' AND ds.total_score >= ?';
      params.push(parseFloat(min_score));
    }

    // Only get open opportunities
    query += " AND sp.deal_stage IN ('Prospecting', 'Engaging')";

    query += ` ORDER BY ds.${sort_by} ${sort_dir}`;
    query += ` LIMIT ${parseInt(limit)} OFFSET ${parseInt(offset)}`;

    const opportunities = db.prepare(query).all(...params);
    res.json(opportunities);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get opportunity details
app.get('/opportunities/:id', (req, res) => {
  try {
    const { id } = req.params;

    const opportunity = db.prepare(`
      SELECT 
        sp.opportunity_id,
        sp.sales_agent,
        sp.product,
        sp.account,
        sp.deal_stage,
        sp.engage_date,
        sp.close_date,
        sp.close_value,
        a.revenue,
        a.employees,
        a.sector,
        a.year_established,
        st.manager,
        st.regional_office,
        p.sales_price,
        ds.total_score,
        ds.stage_score,
        ds.account_score,
        ds.seller_score,
        ds.product_score,
        ds.time_score,
        ds.success_probability
      FROM sales_pipeline sp
      LEFT JOIN accounts a ON sp.account = a.account
      LEFT JOIN sales_teams st ON sp.sales_agent = st.sales_agent
      LEFT JOIN products p ON sp.product = p.product
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.opportunity_id = ?
    `).get(id);

    if (!opportunity) {
      return res.status(404).json({ error: 'Opportunity not found' });
    }

    // Get seller's performance metrics
    const sellerMetrics = db.prepare(`
      SELECT 
        COUNT(*) as total_deals,
        SUM(CASE WHEN deal_stage = 'Won' THEN 1 ELSE 0 END) as won_deals,
        AVG(CASE WHEN deal_stage IN ('Won', 'Lost') THEN ds.total_score ELSE NULL END) as avg_deal_score
      FROM sales_pipeline sp
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.sales_agent = ?
    `).get(opportunity.sales_agent);

    // Get similar deals from same account
    const accountHistory = db.prepare(`
      SELECT 
        sp.opportunity_id,
        sp.deal_stage,
        sp.product,
        sp.close_value,
        sp.close_date,
        ds.total_score
      FROM sales_pipeline sp
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.account = ? AND sp.opportunity_id != ?
      ORDER BY sp.close_date DESC
      LIMIT 5
    `).all(opportunity.account, id);

    res.json({
      ...opportunity,
      seller_metrics: sellerMetrics,
      account_history: accountHistory
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get filters options
app.get('/filters', (req, res) => {
  try {
    const sales_agents = db.prepare(`
      SELECT DISTINCT sales_agent FROM sales_pipeline 
      WHERE deal_stage IN ('Prospecting', 'Engaging')
      ORDER BY sales_agent
    `).all().map(r => r.sales_agent);

    const deal_stages = db.prepare(`
      SELECT DISTINCT deal_stage FROM sales_pipeline
      WHERE deal_stage IN ('Prospecting', 'Engaging')
      ORDER BY deal_stage
    `).all().map(r => r.deal_stage);

    const products = db.prepare(`
      SELECT DISTINCT product FROM sales_pipeline 
      WHERE deal_stage IN ('Prospecting', 'Engaging')
      ORDER BY product
    `).all().map(r => r.product);

    const accounts = db.prepare(`
      SELECT DISTINCT account FROM sales_pipeline 
      WHERE account IS NOT NULL AND deal_stage IN ('Prospecting', 'Engaging')
      ORDER BY account
    `).all().map(r => r.account);

    res.json({
      sales_agents,
      deal_stages,
      products,
      accounts
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get dashboard summary stats
app.get('/stats', (req, res) => {
  try {
    const stats = db.prepare(`
      SELECT 
        COUNT(*) as total_open_deals,
        COUNT(DISTINCT sales_agent) as total_agents,
        ROUND(AVG(ds.total_score), 2) as avg_score,
        ROUND(MAX(ds.total_score), 2) as highest_score,
        ROUND(AVG(ds.success_probability), 3) as avg_success_prob
      FROM sales_pipeline sp
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.deal_stage IN ('Prospecting', 'Engaging')
    `).get();

    const topDeals = db.prepare(`
      SELECT 
        sp.opportunity_id,
        sp.sales_agent,
        sp.account,
        sp.product,
        ds.total_score,
        ds.success_probability
      FROM sales_pipeline sp
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.deal_stage IN ('Prospecting', 'Engaging')
      ORDER BY ds.total_score DESC
      LIMIT 5
    `).all();

    const sellerPerformance = db.prepare(`
      SELECT 
        sp.sales_agent,
        COUNT(*) as deals_count,
        ROUND(AVG(ds.total_score), 2) as avg_score,
        ROUND(AVG(ds.success_probability), 3) as avg_success_prob
      FROM sales_pipeline sp
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.deal_stage IN ('Prospecting', 'Engaging')
      GROUP BY sp.sales_agent
      ORDER BY avg_score DESC
      LIMIT 10
    `).all();

    res.json({
      summary: stats,
      top_deals: topDeals,
      seller_performance: sellerPerformance
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get time on pipeline distribution
app.get('/analytics/time-on-pipeline', (req, res) => {
  try {
    const data = db.prepare(`
      SELECT 
        CASE 
          WHEN julianday('now') - julianday(engage_date) < 30 THEN '0-30 days'
          WHEN julianday('now') - julianday(engage_date) < 60 THEN '30-60 days'
          WHEN julianday('now') - julianday(engage_date) < 90 THEN '60-90 days'
          WHEN julianday('now') - julianday(engage_date) < 120 THEN '90-120 days'
          ELSE '120+ days'
        END as time_range,
        COUNT(*) as count,
        ROUND(AVG(ds.success_probability), 3) as avg_success_prob,
        ROUND(AVG(ds.total_score), 2) as avg_score
      FROM sales_pipeline sp
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.deal_stage IN ('Prospecting', 'Engaging') AND sp.engage_date IS NOT NULL
      GROUP BY time_range
      ORDER BY 
        CASE time_range
          WHEN '0-30 days' THEN 1
          WHEN '30-60 days' THEN 2
          WHEN '60-90 days' THEN 3
          WHEN '90-120 days' THEN 4
          ELSE 5
        END
    `).all();

    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get account size distribution
app.get('/analytics/account-size', (req, res) => {
  try {
    const data = db.prepare(`
      SELECT 
        CASE 
          WHEN a.employees < 100 THEN 'Startup (< 100)'
          WHEN a.employees < 500 THEN 'Small (100-500)'
          WHEN a.employees < 2000 THEN 'Medium (500-2K)'
          WHEN a.employees < 10000 THEN 'Large (2K-10K)'
          ELSE 'Enterprise (10K+)'
        END as size_category,
        COUNT(*) as count,
        ROUND(AVG(ds.success_probability), 3) as avg_success_prob,
        ROUND(AVG(ds.total_score), 2) as avg_score
      FROM sales_pipeline sp
      LEFT JOIN accounts a ON sp.account = a.account
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      WHERE sp.deal_stage IN ('Prospecting', 'Engaging') AND a.employees IS NOT NULL
      GROUP BY size_category
    `).all();

    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get available months for forecast filter
app.get('/analytics/months', (req, res) => {
  try {
    const months = db.prepare(`
      SELECT DISTINCT strftime('%Y-%m', engage_date) as month
      FROM sales_pipeline
      WHERE engage_date IS NOT NULL AND engage_date != ''
      ORDER BY month DESC
    `).all().map(r => r.month).filter(Boolean);

    res.json(months);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get forecast by month
app.get('/analytics/forecast', (req, res) => {
  try {
    const { month } = req.query;

    let openQuery = `
      SELECT 
        COUNT(*) as open_deals,
        ROUND(AVG(ds.success_probability), 3) as avg_probability,
        ROUND(SUM(p.sales_price * ds.success_probability), 0) as weighted_revenue,
        ROUND(SUM(p.sales_price), 0) as pipeline_value,
        SUM(CASE WHEN sp.deal_stage = 'Prospecting' THEN 1 ELSE 0 END) as prospecting_count,
        SUM(CASE WHEN sp.deal_stage = 'Engaging' THEN 1 ELSE 0 END) as engaging_count,
        ROUND(SUM(CASE WHEN sp.deal_stage = 'Prospecting' THEN p.sales_price * ds.success_probability ELSE 0 END), 0) as prospecting_forecast,
        ROUND(SUM(CASE WHEN sp.deal_stage = 'Engaging' THEN p.sales_price * ds.success_probability ELSE 0 END), 0) as engaging_forecast
      FROM sales_pipeline sp
      LEFT JOIN deal_scores ds ON sp.opportunity_id = ds.opportunity_id
      LEFT JOIN products p ON sp.product = p.product
      WHERE sp.deal_stage IN ('Prospecting', 'Engaging')
    `;

    const openParams = [];

    if (month) {
      openQuery += ' AND strftime(\'%Y-%m\', sp.engage_date) = ?';
      openParams.push(month);
    }

    const openForecast = db.prepare(openQuery).get(...openParams);

    // Get actual closed revenue for past months (for context)
    let closedQuery = `
      SELECT 
        COUNT(*) as won_deals,
        ROUND(SUM(sp.close_value), 0) as closed_revenue,
        ROUND(AVG(sp.close_value), 0) as avg_deal_value
      FROM sales_pipeline sp
      WHERE sp.deal_stage = 'Won'
    `;

    const closedParams = [];

    if (month) {
      closedQuery += ' AND strftime(\'%Y-%m\', sp.close_date) = ?';
      closedParams.push(month);
    }

    const closedActual = db.prepare(closedQuery).get(...closedParams);

    res.json({
      month: month || null,
      forecast: openForecast,
      actual: closedActual,
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`🚀 API Server running at http://localhost:${PORT}`);
  console.log(`📊 Dashboard data available at http://localhost:5173`);
});
