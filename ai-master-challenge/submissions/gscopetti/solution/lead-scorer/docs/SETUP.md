# Setup Guide — Lead Scorer

## Quick Start (5 minutes)

### Prerequisites
- **Node.js** 18+ ([download](https://nodejs.org))
- **npm** (comes with Node)
- **git** (optional, for version control)

### Installation

```bash
# 1. Navigate to project directory
cd lead-scorer

# 2. Install dependencies (first time only)
npm install

# 3. Start development server
npm run dev

# 4. Open in browser
# → http://localhost:5173
```

### First Run

1. App opens to **📤 Upload** page
2. Click "📂 Select files" or drag-drop 4 CSVs:
   - `accounts.csv`
   - `products.csv`
   - `sales_teams.csv`
   - `sales_pipeline.csv`
3. Click "📂 Process Data"
4. Wait 3-5 seconds for scoring to complete
5. Redirect to **📊 Painel** (Dashboard)

**You're ready to explore!** 🎉

---

## Project Structure

```
lead-scorer/
├── src/
│   ├── components/
│   │   ├── layout/          # Sidebar, Header, MainContent
│   │   ├── pages/           # Dashboard, Deals, Detail, etc.
│   │   ├── upload/          # Upload interface
│   │   ├── dashboard/       # KPI cards, charts
│   │   └── spin/            # SPIN script viewer
│   ├── hooks/               # React hooks for logic
│   │   ├── useDataLoader    # CSV parsing
│   │   ├── useDealScoring   # Score calculation
│   │   ├── useAccountScoring
│   │   └── useSPINGenerator
│   ├── utils/               # Pure functions
│   │   ├── scoring.ts       # Score algorithms
│   │   ├── normalizer.ts    # Data cleanup
│   │   ├── spin-*           # SPIN templates
│   │   ├── tiers.ts         # Tier classification
│   │   └── filters.ts       # Filter utilities
│   ├── types/               # TypeScript interfaces
│   ├── context/             # Global state (DataContext)
│   └── App.tsx              # Main component
├── docs/                    # Documentation
│   ├── SETUP.md            # This file
│   ├── SCORING_LOGIC.md    # Algorithm explanation
│   └── INTEGRATION_TESTS.md # Test checklist
├── package.json            # Dependencies
└── README.md               # Project overview
```

---

## Available Commands

### Development

```bash
# Start dev server (HMR enabled)
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Type check (no build)
npm run typecheck

# Lint code style
npm run lint
```

### Debugging

```bash
# Open browser DevTools
# Press F12 in any page

# View console logs
# Console tab → Shows parsed data and scores

# Check Network tab
# Verify CSV files load (should be instant)
```

---

## Configuration

### Tailwind CSS
- **Config:** `tailwind.config.js`
- **Colors:** Slate-950 dark theme (slate-900, slate-800, slate-700)
- **Breakpoints:** Mobile-first (lg: 1024px)

### TypeScript
- **Config:** `tsconfig.app.json`
- **Strict mode:** Enabled
- **Path aliases:** `@/*` → `src/*`

### Vite
- **Config:** `vite.config.ts`
- **Dev server:** Auto-refresh on save
- **Build:** Minified + chunked

---

## Customization

### Change Dark Mode Colors

Edit `src/index.css`:
```css
:root {
  --color-primary: #3b82f6;  /* Blue */
  --color-danger: #dc2626;   /* Red */
  /* ... */
}
```

### Adjust Tier Cutoffs

Edit `src/utils/tiers.ts`:
```typescript
if (score >= 80) return 'HOT';     // Change 80 to your threshold
if (score >= 60) return 'WARM';    // etc.
```

### Modify Scoring Weights

Edit `src/hooks/useDealScoring.ts`:
```typescript
const winRateWeight = 20;  // Change from 20 to 25, etc.
const priceWeight = 20;
// ... update and re-run
```

---

## Troubleshooting

### "npm ERR! code ENOENT"
**Issue:** Dependencies not installed
**Fix:**
```bash
rm -rf node_modules package-lock.json
npm install
```

### "Cannot find module '@/types'"
**Issue:** Path alias not working
**Fix:** Restart dev server
```bash
npm run dev
# (stop with Ctrl+C first)
```

### Build fails with "Chunk size warning"
**Issue:** Bundle is 640 KB (large but functional)
**Fix:** Not critical for demo; ignore or implement code-splitting
```bash
npm run build  # Works fine despite warning
```

### Scores not calculating
**Issue:** CSV data might be malformed
**Fix:**
1. Check CSV headers match expected names
2. Open DevTools (F12) → Console
3. Look for validation errors
4. Verify CSV files are plain text (not Excel)

### Dark mode not showing
**Issue:** Browser cached light theme
**Fix:**
```bash
# Hard refresh to clear cache
Windows/Linux: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

---

## Performance Tips

### Faster Load Times
1. Close other browser tabs (reduces memory)
2. Use Chrome/Edge (fastest)
3. Ensure SSD (faster file I/O)

### Smooth Scrolling
- Dashboard: Native scroll (smooth)
- Deals table: Virtual scroll for 2,000+ rows (built-in)
- Keep browser clean (fewer extensions = faster)

### Optimal Development
- Keep dev server running (fast HMR)
- Use Chrome DevTools throttling for mobile testing
- Monitor memory (DevTools → Memory tab)

---

## Deployment

### Build for Production

```bash
npm run build
# Creates: dist/ folder
# Ready to deploy to any static host
```

### Deploy Options

**Option 1: Netlify**
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

**Option 2: Vercel**
```bash
npm install -g vercel
vercel --prod
```

**Option 3: GitHub Pages**
```bash
# Set homepage in package.json
# "homepage": "https://username.github.io/lead-scorer"
npm run build
# Deploy dist/ to gh-pages branch
```

**Option 4: Docker**
```dockerfile
FROM node:18
WORKDIR /app
COPY . .
RUN npm install && npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

---

## Development Workflow

### 1. Make Changes
Edit any file in `src/`

### 2. Hot Reload
Changes appear instantly in browser

### 3. Type Check
```bash
npm run typecheck
# Fix any TypeScript errors
```

### 4. Lint
```bash
npm run lint
# Fix style issues
```

### 5. Build & Test
```bash
npm run build
npm run preview
# Test production build locally
```

### 6. Deploy
```bash
npm run build
# Upload dist/ to hosting
```

---

## Data Requirements

### CSV Format

**accounts.csv**
```csv
account,sector,year_established,revenue,employees,office_location,subsidiary_of
Acme Corp,Technology,2010,5000000,2822,United States,
```

**products.csv**
```csv
product,series,sales_price
GTX Pro,GTX,1234.56
```

**sales_teams.csv**
```csv
sales_agent,manager,regional_office
Moses Frase,John Smith,Central
```

**sales_pipeline.csv**
```csv
opportunity_id,sales_agent,product,account,deal_stage,engage_date,close_date,close_value
OPP-001,Moses Frase,GTX Pro,Acme Corp,Won,2017-03-10,2017-03-15,1234.56
```

### Data Size Expectations

- Accounts: 50-5,000
- Products: 5-100
- Sales teams: 10-500
- Opportunities: 100-50,000

Current dataset: **85 + 7 + 35 + 8,800** (good for demo)

---

## Features Checklist

- [x] CSV upload with validation
- [x] Data normalization (product names, dates)
- [x] Deal scoring (0-100) with 7 factors
- [x] Account scoring with aggregation
- [x] Tier classification (HOT/WARM/COOL/COLD)
- [x] Dashboard with KPIs & charts
- [x] Deals table with sort/filter/search
- [x] Deal detail view with breakdown
- [x] SPIN Selling script generation
- [x] Account rankings
- [x] Sales team performance
- [x] Global filters (region, manager, vendor, tier)
- [x] Dark mode (always on)
- [x] Responsive design
- [x] Full TypeScript + strict mode
- [x] Tailwind CSS styling
- [x] Zero external libraries for charts (Recharts)

---

## Support & Documentation

- **Scoring Logic:** Read `docs/SCORING_LOGIC.md`
- **Integration Tests:** Check `docs/INTEGRATION_TESTS.md`
- **Code Examples:** See `src/hooks/` and `src/utils/`
- **Type Definitions:** Check `src/types/index.ts`

---

## License

MIT — Free to use and modify

---

**Ready to score some deals?** 🚀

```bash
npm run dev
# Happy scoring! 🎯
```
