# Documentation Index

Welcome to the Sales Pipeline Dashboard! This document helps you find the right guide for what you need.

## 📚 Documentation Structure

### For Getting Started (Read First!)

1. **[QUICK_START.md](QUICK_START.md)** ⭐ **START HERE**
   - Simple 3-step setup
   - One command to run everything
   - Best for first-time users
   - **Time:** 5 minutes

2. **[README.md](README.md)** 
   - Complete feature overview
   - How to use every feature
   - Understanding scores
   - Troubleshooting basics
   - **Time:** 15 minutes

### For Understanding the Scoring

3. **[SCORING_FORMULA.md](SCORING_FORMULA.md)**
   - Detailed scoring algorithm explanation
   - Example scorecards
   - What each score means
   - How to interpret results
   - **Time:** 10 minutes

### For Technical Details

4. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - System architecture diagram
   - Database schema
   - API endpoints
   - Development guide
   - **For:** Developers only
   - **Time:** 20 minutes

### For Problem Solving

5. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**
   - Solutions to common problems
   - Error message explanations
   - Performance tips
   - Debug information
   - **When:** Something isn't working
   - **Time:** 5-10 minutes

---

## 🎯 Quick Navigation by User Type

### I'm a Sales Agent (Non-Technical)
1. Start with [QUICK_START.md](QUICK_START.md)
2. Learn features in [README.md](README.md)
3. Understand scores in [SCORING_FORMULA.md](SCORING_FORMULA.md)
4. If problems: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### I'm a Sales Manager
1. Same as Sales Agent above
2. Focus on "Top Sales Agents" section in README
3. Review "Analytics" tab for performance insights

### I'm a System Administrator / IT
1. Read [QUICK_START.md](QUICK_START.md) for setup
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for maintenance
4. Plan deployment strategy

### I'm a Developer / Data Analyst
1. Review [ARCHITECTURE.md](ARCHITECTURE.md) - system design
2. Study [SCORING_FORMULA.md](SCORING_FORMULA.md) - algorithm
3. Check source code in `src/` and `server/` folders
4. Modify scoring in `scripts/load-data.mjs`

---

## 📋 Feature Summary

### 🎯 Core Features
- ✅ Smart deal scoring (0-100)
- ✅ Success probability calculation
- ✅ Interactive dashboard
- ✅ Detailed score breakdown
- ✅ Real-time filtering
- ✅ Advanced sorting
- ✅ Analytics & charts
- ✅ Deal details modal
- ✅ Seller performance tracking

### 🔍 Filters Available
- Sales Agent
- Deal Stage
- Product
- Account (search)
- Minimum Score

### 📊 Analytics Available
- Top scoring deals
- Top performing agents
- Deal duration impact
- Company size impact
- KPI summary cards

### 🎨 User Interface
- Clean, modern design
- Responsive layout (desktop & tablet)
- Color-coded scores
- Interactive charts
- Detailed modals

---

## ⚡ Quick Commands Reference

### One-Time Setup
```bash
./setup.sh              # Mac/Linux
setup.bat              # Windows
```

### Start Dashboard
```bash
npm start              # Best option - starts everything
```

### Alternative: Run Separately
```bash
npm run server         # Terminal 1 - API server
npm run dev            # Terminal 2 - Dev dashboard
```

### Development
```bash
npm install            # Install dependencies
npm run setup          # Load data from CSVs
npm run build          # Build for production
```

---

## 🎓 Learning Path

### Beginner (Total: 30 minutes)
1. Read QUICK_START.md (5 min)
2. Run setup.sh (5 min)
3. Explore dashboard (10 min)
4. Read README.md features section (10 min)

### Intermediate (Total: 1 hour)
1. Complete Beginner path (30 min)
2. Read SCORING_FORMULA.md (10 min)
3. Explore Analytics tab (10 min)
4. Try all filters and features (10 min)

### Advanced (Total: 2 hours)
1. Complete Intermediate path (1 hour)
2. Read ARCHITECTURE.md (20 min)
3. Review source code (20 min)
4. Customize scoring or features (20 min)

---

## 🔗 File Structure for Reference

```
📁 sales-dashboard/
├── 📄 QUICK_START.md          ← Start here!
├── 📄 README.md               ← Full user guide
├── 📄 SCORING_FORMULA.md      ← How scores work
├── 📄 ARCHITECTURE.md         ← Technical details
├── 📄 TROUBLESHOOTING.md      ← Problem solving
├── 📄 INDEX.md                ← You are here
├── 📁 src/                    ← React app code
├── 📁 server/                 ← API server code
├── 📁 scripts/                ← Setup scripts
├── 📁 data/                   ← SQLite database
├── 📄 package.json            ← Dependencies
└── 📄 index.html              ← Entry page
```

---

## ❓ FAQ

### Q: Where do I start?
**A:** Start with [QUICK_START.md](QUICK_START.md)

### Q: How long does setup take?
**A:** About 5-10 minutes depending on internet speed

### Q: Can I customize the scoring?
**A:** Yes! See [ARCHITECTURE.md](ARCHITECTURE.md) for details

### Q: What if setup fails?
**A:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Q: Do I need internet access?
**A:** Only during npm install. Dashboard runs locally after that.

### Q: Can I share the data?
**A:** Database is local. Copy the entire folder to share.

### Q: How do I update the data?
**A:** Replace CSV files and run `npm run setup`

### Q: What if a deal score changes?
**A:** Scores recalculate when seller/product performance changes

---

## 🚀 Next Steps

**Ready to begin?** Follow this path:

1. → Open [QUICK_START.md](QUICK_START.md)
2. → Run setup.sh (or setup.bat on Windows)
3. → Open http://localhost:5173
4. → Explore your deals!

---

## 💡 Pro Tips

### For Getting the Most Out of Dashboard:
- Click ANY score to see why it's accurate
- Use filters to focus on priority deals
- Check Analytics tab for trends
- Review seller performance for coaching
- Monitor account history for patterns

### For Best Performance:
- Run setup once per week to get fresh scores
- Keep browser updated
- Close unused tabs
- Restart servers if sluggish

### For Problem-Solving:
- Restart servers first (fixes 80% of issues)
- Check browser console (F12)
- Read TROUBLESHOOTING.md
- Collect screenshots and error messages

---

## 📞 Support Resources

- **Most Common Issues?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **How does scoring work?** → [SCORING_FORMULA.md](SCORING_FORMULA.md)
- **How do I set it up?** → [QUICK_START.md](QUICK_START.md)
- **How do I use it?** → [README.md](README.md)
- **Technical questions?** → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## ✅ Checklist: First-Time Setup

- [ ] Downloaded Node.js from nodejs.org
- [ ] Opened terminal in sales-dashboard folder
- [ ] Ran setup.sh (Mac/Linux) or setup.bat (Windows)
- [ ] Waited for setup to complete (no errors)
- [ ] Opened browser to http://localhost:5173
- [ ] See dashboard with deals listed
- [ ] Read QUICK_START.md
- [ ] Ready to prioritize your pipeline! ✨

---

**You're all set! Happy selling! 🎉**

Questions? Problems? Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first!

