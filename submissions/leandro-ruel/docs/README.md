# Sales Pipeline Dashboard

A modern, interactive sales pipeline dashboard that helps sales teams prioritize deals based on success probability and comprehensive scoring.

## 🎯 Key Features

- **Smart Scoring Formula**: Combines multiple factors to calculate deal success probability
  - Deal Stage (0-25 points): Progress through Prospecting → Engaging → Won
  - Account Size (0-20 points): Company revenue and employee count
  - Seller Performance (0-20 points): Sales agent's historical win rate
  - Product Performance (0-20 points): Product's historical success rate
  - Time on Pipeline (0-15 points): Optimal cycle time is 100-120 days

- **Interactive Dashboard**
  - View all deals ranked by score
  - Click any score to see detailed breakdown
  - Real-time analytics and charts
  - KPI summary cards

- **Advanced Filters**
  - Filter by Sales Agent, Deal Stage, Product, Account, or Minimum Score
  - Search and sort deals instantly
  - Reset filters with one click

- **Analytics & Insights**
  - Top performing deals
  - Sales agent performance comparison
  - Deal duration impact analysis
  - Company size impact on success

- **Deal Details**
  - Comprehensive score breakdown
  - Seller performance metrics
  - Account profile and history
  - Related deals from same account

## 🚀 Quick Start (for non-programmers)

### Prerequisites
- **Node.js** (Download from https://nodejs.org/ - choose LTS version)
- **Web Browser** (Chrome, Firefox, Safari, or Edge)

### One-Command Setup

1. Open Terminal/Command Prompt and navigate to this folder
2. Run:
```bash
./setup.sh
```

Or on Windows, double-click `setup.bat`

### Start the Dashboard

After setup, you have two options:

**Option 1: One Command (Easiest)**
```bash
npm start
```

**Option 2: Two Separate Terminals**

Terminal 1:
```bash
npm run server
```

Terminal 2:
```bash
npm run dev
```

### Access the Dashboard
Open your web browser and go to: **http://localhost:5173**

## 📊 Understanding the Score

Each deal gets a score from 0-100 based on:

| Factor | Max Points | What It Measures |
|--------|-----------|------------------|
| **Deal Stage** | 25 | How far along in the pipeline (Prospecting=5, Engaging=15, Won=25) |
| **Account Size** | 20 | Company size (revenue + employee count) |
| **Seller Performance** | 20 | Sales agent's historical win rate with similar deals |
| **Product Performance** | 20 | How often this product converts to sales |
| **Time on Pipeline** | 15 | Deal velocity (rewards 100-120 day cycles) |

### Score Ratings
- **75-100**: Excellent - High priority, likely to close
- **60-74**: Good - Medium-high priority, monitor closely
- **45-59**: Fair - Monitor, may need intervention
- **0-44**: Poor - Low priority or high risk

## 💡 How to Use

### View Your Pipeline
1. Go to the "Pipeline" tab
2. See all open opportunities ranked by success score (highest first)
3. Deals are color-coded:
   - 🟢 Green: Excellent score
   - 🔵 Blue: Good score
   - 🟡 Yellow: Fair score
   - 🔴 Red: Poor score

### Find High-Priority Deals
1. Click on any score badge to see why that score makes sense
2. The breakdown shows exactly which factors helped or hurt the score
3. Click "View" to see detailed information about the account and seller

### Use Filters to Focus
- **Sales Agent**: See deals for a specific team member
- **Deal Stage**: Filter by Prospecting or Engaging
- **Product**: Focus on specific product lines
- **Account**: Search for specific companies
- **Min Score**: Show only high-probability deals

### Understand Deal Details

Click "View" on any deal to see:
- **Score Breakdown**: Visual breakdown of all scoring factors
- **Seller Performance**: How well this agent performs
- **Account Profile**: Company size, industry, age
- **Account History**: Previous deals with this company
- **Success Probability**: Estimated chance of closing

### Analyze Trends

Go to the "Analytics" tab to see:
- **Top Deals**: Your best opportunities right now
- **Top Agents**: Highest-performing sales team members
- **Deal Duration**: How long deals typically take
- **Company Size Impact**: How account size affects success

## 📁 Project Structure

```
sales-dashboard/
├── src/
│   ├── App.jsx                  # Main app component
│   ├── main.jsx                 # React entry point
│   ├── index.css                # Styles
│   ├── api/
│   │   └── client.js            # API client
│   ├── components/
│   │   ├── Dashboard.jsx        # Dashboard & analytics
│   │   ├── FilterBar.jsx        # Filters component
│   │   ├── OpportunitiesTable.jsx # Deal table & modal
│   │   └── ScoreDisplay.jsx     # Score visualization
│   └── utils/
│       └── formatting.js        # Formatting helpers
├── server/
│   └── api.mjs                  # Node.js API server
├── scripts/
│   ├── setup.mjs                # Data loader script
│   └── setup.sh                 # Setup script
├── data/                        # Database (created after setup)
├── package.json                 # Dependencies
├── vite.config.js               # Vite configuration
├── index.html                   # HTML entry point
└── README.md                    # This file
```

## 🔧 Commands Reference

| Command | What It Does |
|---------|--------------|
| `npm start` | Start both servers (easiest) |
| `npm run dev` | Start Vite dev server (port 5173) |
| `npm run server` | Start API server (port 3001) |
| `npm run setup` | Load data from CSV files |
| `npm install` | Install dependencies |
| `npm run build` | Build for production |

## 📊 Data Source

The dashboard loads data from:
- `sales_pipeline.csv` - All opportunities
- `accounts.csv` - Company information
- `products.csv` - Product details
- `sales_teams.csv` - Sales agent information
- `metadata.csv` - Field descriptions

The data is imported into SQLite when you run setup.

## 🎨 Technologies Used

- **Frontend**: React 18 + Vite
- **Database**: SQLite
- **API**: Express.js
- **Charts**: Recharts
- **UI Components**: shadcn/ui
- **Icons**: Lucide React
- **Styling**: Tailwind CSS

## ❓ Troubleshooting

### "npm command not found"
- Node.js is not installed
- Download and install from https://nodejs.org/

### "Port 3001 or 5173 already in use"
- Another application is using these ports
- Change ports in `vite.config.js` and `server/api.mjs`
- Or close the application using these ports

### "Database not found"
- Run `npm run setup` to load the data
- Check that CSV files are in the correct location

### "API errors when clicking on deals"
- Make sure API server is running: `npm run server`
- Check browser console for error messages (F12)

## 📈 How Scoring Works

The scoring algorithm analyzes historical sales data to:

1. **Calculate win rates** for each seller and product
2. **Measure account quality** by size (employees, revenue)
3. **Track deal velocity** to identify optimal cycle times
4. **Combine factors** with weighted formula
5. **Generate probability** of closing (0-100%)

Example: A deal might score high because:
- It's in Engaging stage (+15 points)
- The seller has a 70% win rate (+14 points)
- The product usually closes 60% of the time (+12 points)
- The account is large with 2000+ employees (+18 points)
- Total: 59/100 = Good chance of closing

## 📞 Support

If you encounter issues:

1. Check the browser console (Press F12, go to "Console" tab)
2. Make sure both servers are running
3. Try refreshing the page
4. Restart the servers: Stop all and run `npm start` again

## 📝 Notes

- No authentication required - internal tool for your team
- Data is stored locally in SQLite
- All scoring calculations happen in real-time
- Historical data is not modified - read-only access

## 🎓 Learning the Formula

The scoring formula is explained in detail when you click any score in the dashboard. Each component is calculated based on:

- **Historical performance**: What happened with similar deals
- **Account characteristics**: Size, age, industry
- **Product factors**: Category, pricing tier, market demand
- **Seller expertise**: Win rate, average deal size, velocity

The system learns from your data and weights each factor accordingly.

---

**Happy selling! 🎉**

For questions or improvements, contact your data analytics team.
