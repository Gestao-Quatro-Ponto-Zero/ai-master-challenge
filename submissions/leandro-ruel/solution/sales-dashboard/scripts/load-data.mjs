import fs from 'fs';
import path from 'path';
import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const dbPath = path.join(__dirname, '../data/sales.db');
const dataPath = path.join(__dirname, '../../dataset');

// Ensure data directory exists
if (!fs.existsSync(path.dirname(dbPath))) {
  fs.mkdirSync(path.dirname(dbPath), { recursive: true });
}

// Remove existing database
if (fs.existsSync(dbPath)) {
  fs.unlinkSync(dbPath);
}

const db = new Database(dbPath);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = OFF');

// Create tables
db.exec(`
  CREATE TABLE accounts (
    account TEXT PRIMARY KEY,
    sector TEXT,
    year_established INTEGER,
    revenue REAL,
    employees INTEGER,
    office_location TEXT,
    subsidiary_of TEXT
  );

  CREATE TABLE products (
    product TEXT PRIMARY KEY,
    series TEXT,
    sales_price REAL
  );

  CREATE TABLE sales_teams (
    sales_agent TEXT PRIMARY KEY,
    manager TEXT,
    regional_office TEXT
  );

  CREATE TABLE sales_pipeline (
    opportunity_id TEXT PRIMARY KEY,
    sales_agent TEXT,
    product TEXT,
    account TEXT,
    deal_stage TEXT,
    engage_date TEXT,
    close_date TEXT,
    close_value REAL,
    FOREIGN KEY (sales_agent) REFERENCES sales_teams(sales_agent),
    FOREIGN KEY (product) REFERENCES products(product),
    FOREIGN KEY (account) REFERENCES accounts(account)
  );

  CREATE TABLE deal_scores (
    opportunity_id TEXT PRIMARY KEY,
    total_score REAL,
    stage_score REAL,
    account_score REAL,
    seller_score REAL,
    product_score REAL,
    time_score REAL,
    success_probability REAL,
    FOREIGN KEY (opportunity_id) REFERENCES sales_pipeline(opportunity_id)
  );

  CREATE INDEX idx_sales_agent ON sales_pipeline(sales_agent);
  CREATE INDEX idx_deal_stage ON sales_pipeline(deal_stage);
  CREATE INDEX idx_account ON sales_pipeline(account);
  CREATE INDEX idx_product ON sales_pipeline(product);
  CREATE INDEX idx_total_score ON deal_scores(total_score DESC);
`);

// Load CSV files
function loadCSV(filename) {
  const filePath = path.join(dataPath, filename);
  const content = fs.readFileSync(filePath, 'utf-8');
  return content.trim().split('\n').map((line, index) => {
    if (index === 0) return null;
    const parts = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') {
        inQuotes = !inQuotes;
      } else if (line[i] === ',' && !inQuotes) {
        parts.push(current);
        current = '';
      } else {
        current += line[i];
      }
    }
    parts.push(current);
    return parts;
  }).filter(Boolean);
}

console.log('Loading CSV files...');

// Load accounts
const accountsData = loadCSV('accounts.csv');
const insertAccount = db.prepare(
  'INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?)'
);
const accountsStmt = db.transaction((data) => {
  for (const row of data) {
    insertAccount.run(
      row[0], row[1], parseInt(row[2]), parseFloat(row[3]), 
      parseInt(row[4]), row[5], row[6] || null
    );
  }
});
accountsStmt(accountsData);
console.log(`Loaded ${accountsData.length} accounts`);

// Load products
const productsData = loadCSV('products.csv');
const insertProduct = db.prepare(
  'INSERT INTO products VALUES (?, ?, ?)'
);
const productsStmt = db.transaction((data) => {
  for (const row of data) {
    insertProduct.run(row[0], row[1], parseFloat(row[2]));
  }
});
productsStmt(productsData);
console.log(`Loaded ${productsData.length} products`);

// Load sales teams
const teamsData = loadCSV('sales_teams.csv');
const insertTeam = db.prepare(
  'INSERT INTO sales_teams VALUES (?, ?, ?)'
);
const teamsStmt = db.transaction((data) => {
  for (const row of data) {
    insertTeam.run(row[0], row[1], row[2]);
  }
});
teamsStmt(teamsData);
console.log(`Loaded ${teamsData.length} sales agents`);

// Load sales pipeline
const pipelineData = loadCSV('sales_pipeline.csv');
const insertPipeline = db.prepare(
  'INSERT INTO sales_pipeline VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
);
const pipelineStmt = db.transaction((data) => {
  for (const row of data) {
    insertPipeline.run(
      row[0], row[1], row[2], row[3] || null, row[4], 
      row[5], row[6] || null, row[7] ? parseFloat(row[7]) : 0
    );
  }
});
pipelineStmt(pipelineData);
console.log(`Loaded ${pipelineData.length} pipeline opportunities`);

// Calculate scores for all opportunities
console.log('Calculating deal scores...');

// Get statistics for scoring
const stats = db.prepare(`
  SELECT 
    COUNT(*) as total_deals,
    SUM(CASE WHEN deal_stage = 'Won' THEN 1 ELSE 0 END) as won_deals,
    SUM(CASE WHEN deal_stage = 'Lost' THEN 1 ELSE 0 END) as lost_deals,
    AVG(CASE WHEN deal_stage = 'Won' THEN close_value ELSE 0 END) as avg_deal_value,
    MAX(close_value) as max_deal_value
  FROM sales_pipeline
  WHERE close_value > 0
`).all()[0];

const opportunities = db.prepare(`
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
    p.sales_price
  FROM sales_pipeline sp
  LEFT JOIN accounts a ON sp.account = a.account
  LEFT JOIN sales_teams st ON sp.sales_agent = st.sales_agent
  LEFT JOIN products p ON sp.product = p.product
`).all();

// Seller performance cache
const sellerStats = {};
db.prepare(`
  SELECT 
    sales_agent,
    COUNT(*) as deals,
    SUM(CASE WHEN deal_stage = 'Won' THEN 1 ELSE 0 END) as won,
    AVG(CASE WHEN deal_stage = 'Won' THEN close_value ELSE 0 END) as avg_value
  FROM sales_pipeline
  GROUP BY sales_agent
`).all().forEach(row => {
  sellerStats[row.sales_agent] = {
    total_deals: row.deals,
    won_deals: row.won,
    win_rate: row.deals > 0 ? row.won / row.deals : 0,
    avg_deal_value: row.avg_value || 0
  };
});

// Product performance cache
const productStats = {};
db.prepare(`
  SELECT 
    product,
    COUNT(*) as deals,
    SUM(CASE WHEN deal_stage = 'Won' THEN 1 ELSE 0 END) as won,
    AVG(close_value) as avg_value
  FROM sales_pipeline
  WHERE close_value > 0
  GROUP BY product
`).all().forEach(row => {
  productStats[row.product] = {
    total_deals: row.deals,
    won_deals: row.won,
    win_rate: row.deals > 0 ? row.won / row.deals : 0,
    avg_deal_value: row.avg_value || 0
  };
});

const insertScore = db.prepare(
  'INSERT INTO deal_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
);

function calculateScores(opp) {
  // 1. Deal Stage Score (0-25)
  const stageScores = {
    'Prospecting': 5,
    'Engaging': 15,
    'Won': 25,
    'Lost': 0
  };
  const stage_score = stageScores[opp.deal_stage] || 0;

  // 2. Account Score (0-20) - based on size and stability
  let account_score = 0;
  if (opp.employees && opp.revenue) {
    const sizeScore = Math.min(10, (opp.employees / 10000) * 10);
    const revenueScore = Math.min(10, (opp.revenue / 5000) * 10);
    account_score = (sizeScore + revenueScore) / 2;
  }

  // 3. Seller Score (0-20) - based on historical performance
  let seller_score = 0;
  if (sellerStats[opp.sales_agent]) {
    const seller = sellerStats[opp.sales_agent];
    seller_score = Math.min(20, seller.win_rate * 20 + (seller.avg_deal_value / stats.avg_deal_value) * 5);
  }

  // 4. Product Score (0-20) - based on product performance
  let product_score = 0;
  if (productStats[opp.product]) {
    const product = productStats[opp.product];
    product_score = Math.min(20, product.win_rate * 20);
  }

  // 5. Time Score (0-15) - time on pipeline (optimal is 100-120 days)
  let time_score = 0;
  if (opp.engage_date) {
    const engageDate = new Date(opp.engage_date);
    const daysOnPipeline = Math.floor((new Date() - engageDate) / (1000 * 60 * 60 * 24));
    
    if (opp.deal_stage === 'Won' || opp.deal_stage === 'Lost') {
      // Closed deals: use close_date
      const closeDate = new Date(opp.close_date);
      const cycleTime = Math.floor((closeDate - engageDate) / (1000 * 60 * 60 * 24));
      if (cycleTime >= 60 && cycleTime <= 150) {
        time_score = 15;
      } else if (cycleTime > 150) {
        time_score = Math.max(0, 15 - (cycleTime - 150) / 50);
      } else {
        time_score = (cycleTime / 60) * 15;
      }
    } else {
      // Open deals: penalize if too long
      if (daysOnPipeline <= 120) {
        time_score = (daysOnPipeline / 120) * 15;
      } else {
        time_score = Math.max(0, 15 - (daysOnPipeline - 120) / 50);
      }
    }
  }

  const total_score = stage_score + account_score + seller_score + product_score + time_score;
  const success_probability = Math.min(1, total_score / 100);

  return {
    stage_score: Math.round(stage_score * 10) / 10,
    account_score: Math.round(account_score * 10) / 10,
    seller_score: Math.round(seller_score * 10) / 10,
    product_score: Math.round(product_score * 10) / 10,
    time_score: Math.round(time_score * 10) / 10,
    total_score: Math.round(total_score * 10) / 10,
    success_probability: Math.round(success_probability * 1000) / 1000
  };
}

const scoresStmt = db.transaction((data) => {
  for (const opp of data) {
    const scores = calculateScores(opp);
    insertScore.run(
      opp.opportunity_id,
      scores.total_score,
      scores.stage_score,
      scores.account_score,
      scores.seller_score,
      scores.product_score,
      scores.time_score,
      scores.success_probability
    );
  }
});
scoresStmt(opportunities);

console.log(`Calculated scores for ${opportunities.length} opportunities`);
console.log('Database setup completed successfully!');
console.log(`Database location: ${dbPath}`);

// Re-enable foreign keys
db.pragma('foreign_keys = ON');
db.close();
