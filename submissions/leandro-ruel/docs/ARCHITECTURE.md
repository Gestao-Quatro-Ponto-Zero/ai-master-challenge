# Sales Dashboard - Architecture & Development Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser (5173)                       │
│  React Dashboard (React + Vite + Recharts + shadcn/ui)      │
└─────────────────────────────────────────────────────────────┘
                              ↕
                         (Axios API)
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              Node.js API Server (3001)                      │
│              Express.js REST API                            │
└─────────────────────────────────────────────────────────────┘
                              ↕
                           (SQL)
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              SQLite Database (sales.db)                     │
│   • sales_pipeline  • accounts  • products                  │
│   • sales_teams     • deal_scores                           │
└─────────────────────────────────────────────────────────────┘
                              ↕
                         (Import)
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   CSV Data Files                            │
│   (from /solution/dataset/)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Frontend (React + Vite)

**Location:** `src/`

#### Key Files:
- `App.jsx` - Main application component with tab navigation
- `components/Dashboard.jsx` - Stats cards, charts, top deals
- `components/FilterBar.jsx` - Filter controls
- `components/OpportunitiesTable.jsx` - Deal list and modal details
- `components/ScoreDisplay.jsx` - Score badge and breakdown visualization
- `api/client.js` - Axios API client
- `utils/formatting.js` - Formatting helpers

#### Libraries:
- **React 18**: UI framework
- **Vite**: Build tool and dev server
- **Recharts**: Charts and visualizations
- **Radix UI**: Accessible components
- **Tailwind CSS**: Styling
- **Lucide React**: Icons
- **shadcn/ui**: Pre-built UI components

#### Flow:
```
User Input (Filter/Sort/Click) 
    ↓
React State Update
    ↓
API Call via axios
    ↓
Fetch Data from Server
    ↓
Render Components with new data
```

### 2. Backend (Node.js + Express)

**Location:** `server/api.mjs`

#### Key Endpoints:

```
GET /opportunities
- Returns open deals with scores
- Filters: sales_agent, deal_stage, account, product, min_score
- Sorting: sort_by (total_score, sales_agent, etc.)

GET /opportunities/:id
- Returns detailed deal information
- Includes: seller metrics, account history, score breakdown

GET /filters
- Returns available filter options
- Used to populate filter dropdowns

GET /stats
- Returns dashboard summary stats
- Top deals, seller performance, KPIs

GET /analytics/time-on-pipeline
- Deals grouped by duration ranges
- Success probability by duration

GET /analytics/account-size
- Deals grouped by company size
- Success probability by size

GET /health
- Health check endpoint
```

#### Technology:
- **Express.js**: REST API framework
- **better-sqlite3**: SQLite database driver
- **CORS**: Cross-origin resource sharing
- **JSON**: Data format

### 3. Database (SQLite)

**Location:** `data/sales.db` (created during setup)

#### Tables:

```sql
accounts
├─ account (PK)
├─ sector
├─ year_established
├─ revenue
├─ employees
├─ office_location
└─ subsidiary_of

products
├─ product (PK)
├─ series
└─ sales_price

sales_teams
├─ sales_agent (PK)
├─ manager
└─ regional_office

sales_pipeline
├─ opportunity_id (PK)
├─ sales_agent (FK)
├─ product (FK)
├─ account (FK)
├─ deal_stage
├─ engage_date
├─ close_date
└─ close_value

deal_scores
├─ opportunity_id (PK/FK)
├─ total_score
├─ stage_score
├─ account_score
├─ seller_score
├─ product_score
├─ time_score
└─ success_probability
```

#### Indexes:
```sql
idx_sales_agent         -- Fast agent filtering
idx_deal_stage          -- Fast stage filtering
idx_account             -- Fast account lookups
idx_product             -- Fast product lookups
idx_total_score DESC    -- Fast sorting by score
```

### 4. Data Loading Pipeline

**Location:** `scripts/load-data.mjs`

#### Process:
1. Read CSV files from `../solution/dataset/`
2. Create SQLite database at `data/sales.db`
3. Create tables with proper schema
4. Load data into tables:
   - accounts.csv → accounts table
   - products.csv → products table
   - sales_teams.csv → sales_teams table
   - sales_pipeline.csv → sales_pipeline table
5. Calculate scores for all opportunities
6. Store calculated scores in deal_scores table

#### Scoring Logic:
For each opportunity:
- Calculate stage_score (0-25)
- Calculate account_score (0-20) based on size
- Calculate seller_score (0-20) based on win rate
- Calculate product_score (0-20) based on product history
- Calculate time_score (0-15) based on pipeline duration
- Sum all scores: total_score (0-100)
- Calculate success_probability (total_score / 100)

## Development Workflow

### Local Development

1. **Terminal 1 - API Server:**
```bash
npm run server
```
Runs on `http://localhost:3001`

2. **Terminal 2 - Dev Server:**
```bash
npm run dev
```
Runs on `http://localhost:5173` with hot reload

### Building for Production

```bash
npm run build
```
Creates optimized build in `dist/` folder

### Deployment

The frontend and backend can be deployed separately:

**Frontend (dist folder):**
- Deploy to any static hosting (Netlify, Vercel, S3, etc.)
- Update API URL in environment variables

**Backend (server/api.mjs):**
- Deploy to Node.js hosting (Heroku, Railway, AWS Lambda, etc.)
- Ensure database path is writable

## Scoring Algorithm Details

### Stage Score Calculation:
```javascript
const stageScores = {
  'Prospecting': 5,
  'Engaging': 15,
  'Won': 25,
  'Lost': 0
};
stage_score = stageScores[deal_stage];
```

### Account Score Calculation:
```javascript
const sizeScore = Math.min(10, (employees / 10000) * 10);
const revenueScore = Math.min(10, (revenue / 5000) * 10);
account_score = (sizeScore + revenueScore) / 2;
```

### Seller Score Calculation:
```javascript
const winRate = won_deals / total_deals;
const relativeValue = avg_deal_value / portfolio_avg_value;
seller_score = Math.min(20, winRate * 20 + relativeValue * 5);
```

### Product Score Calculation:
```javascript
const productWinRate = product_won / product_total;
product_score = Math.min(20, productWinRate * 20);
```

### Time Score Calculation:
```javascript
if (cycle_time <= 120) {
  time_score = (cycle_time / 120) * 15;
} else {
  time_score = Math.max(0, 15 - ((cycle_time - 120) / 50));
}
```

## Performance Considerations

### Database Optimization:
- Indexes on frequently queried columns
- Prepared statements for all queries
- WAL (Write-Ahead Logging) enabled
- Readonly mode for API queries

### API Optimization:
- Pagination support (limit/offset)
- Indexed queries for fast filtering
- Calculated scores stored (not calculated per request)
- CORS enabled for cross-origin requests

### Frontend Optimization:
- React component memoization
- Vite code splitting
- Recharts for efficient charting
- CSS-in-JS for dynamic styling

## Extensibility

### Adding New Scoring Factors:

1. **Add calculation in `load-data.mjs`:**
```javascript
const new_factor_score = calculateNewFactor(opp);
```

2. **Store in database:**
```javascript
const insertScore = db.prepare(
  'INSERT INTO deal_scores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
);
```

3. **Update deal_scores table schema**

4. **Display in UI:**
```jsx
<ScoreBreakdown
  {...scores}
  new_factor_score={new_factor_score}
/>
```

### Adding New API Endpoints:

1. **Add in `server/api.mjs`:**
```javascript
app.get('/new-endpoint', (req, res) => {
  // Query database
  // Return JSON
});
```

2. **Call from frontend:**
```javascript
const { data } = await api.get('/new-endpoint');
```

### Adding New Filters:

1. **Update `FilterBar.jsx` with new filter UI**
2. **Add filter parameter to opportunities query in API**
3. **Update `OpportunitiesTable.jsx` to handle filter**

## Troubleshooting

### Database Issues:
- Delete `data/sales.db` and run setup again
- Check file permissions in `data/` directory

### API Connection Issues:
- Ensure both servers are running
- Check ports 3001 and 5173 are available
- Review browser console for CORS errors

### Performance Issues:
- Check database indexes are created
- Consider limiting query results with LIMIT/OFFSET
- Profile with browser DevTools

## File Structure

```
sales-dashboard/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx       (Stats, charts)
│   │   ├── FilterBar.jsx       (Filter controls)
│   │   ├── OpportunitiesTable.jsx (Deal table, modal)
│   │   └── ScoreDisplay.jsx    (Score visualization)
│   ├── api/
│   │   └── client.js           (API client)
│   ├── utils/
│   │   └── formatting.js       (Formatters)
│   ├── App.jsx                 (Main app)
│   ├── main.jsx                (Entry point)
│   └── index.css               (Styles)
├── server/
│   └── api.mjs                 (Express API)
├── scripts/
│   ├── load-data.mjs           (Data loader)
│   ├── setup.mjs               (Setup orchestrator)
│   ├── setup.sh                (Mac/Linux setup)
│   └── setup.bat               (Windows setup)
├── data/
│   └── sales.db                (SQLite database)
├── package.json                (Dependencies)
├── vite.config.js              (Vite config)
├── tailwind.config.js          (Tailwind config)
├── index.html                  (HTML entry)
├── README.md                   (Full docs)
├── QUICK_START.md              (Quick guide)
├── SCORING_FORMULA.md          (Scoring details)
└── .gitignore                  (Git ignore)
```

## Dependencies Overview

### Production:
- **react**: UI library
- **react-dom**: React renderer
- **express**: API framework
- **cors**: CORS middleware
- **better-sqlite3**: Database driver
- **recharts**: Charting library
- **axios**: HTTP client
- **@radix-ui/**:Accessible components
- **lucide-react**: Icons
- **tailwindcss**: CSS framework

### Development:
- **vite**: Build tool
- **@vitejs/plugin-react**: React plugin
- **autoprefixer**: CSS autoprefixer
- **postcss**: CSS processor

## Security Notes

- No authentication required (internal tool)
- Database is read-only for API queries
- CORS configured for localhost only
- No sensitive data in URLs
- Database file should be protected at OS level

---

For user-facing documentation, see `README.md` and `QUICK_START.md`.

