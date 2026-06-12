# 🚀 QUICK START GUIDE

## For Non-Technical Users

### 🟢 EASIEST — One Command (recommended)

Open a terminal in the `solution` folder and run:

**Mac/Linux:**
```bash
bash start.sh
```

**Windows:**
```
start.bat
```

The script will:
- Check if Node.js is installed (guides you if not)
- Install dependencies automatically
- Load data from CSV files
- Start both servers
- Open the dashboard in your browser

> No need to run separate setup or start commands.

---

### Step-by-Step Alternative

If you prefer to run things manually:

### Step 1: One-Time Setup (5 minutes)

1. **Open Terminal/Command Prompt** in the `sales-dashboard` folder

   - **Mac/Linux**: Right-click in folder → "Open Terminal Here"
   - **Windows**: Right-click in folder → "Open PowerShell window here"

2. **Run the setup script:**

   **Mac/Linux:**
   ```
   bash setup.sh
   ```

   **Windows:**
   - Double-click `setup.bat` file
   - OR type: `setup.bat`

3. **Wait for it to complete** - it will download packages and load your data

### Step 2: Start the Dashboard

After setup completes, choose ONE method:

#### Run Everything Together:
```
npm start
```
Then open http://localhost:5173 in your browser

#### Alternative - Run in Two Windows:
**Window 1:**
```
npm run server
```

**Window 2:**
```
npm run dev
```
Then open http://localhost:5173 in your browser

## ✨ That's It!

You should now see the Sales Pipeline Dashboard with all your deals ranked by success score.

### Common Actions:

- **See your best deals**: Look at the top of the Pipeline tab - highest scores first
- **Find a specific deal**: Use the Filters (Sales Agent, Product, Account, etc.)
- **Understand a score**: Click on any score number - it shows exactly why
- **See analytics**: Click the "Analytics" tab at the top

## 🆘 Need Help?

**"Command not found"** → Make sure you're in the `sales-dashboard` folder

**"Port already in use"** → Close other applications or wait a minute

**"Blank page"** → Try pressing F5 to refresh your browser

**"API error"** → Make sure both servers are running

For other issues, check the full README.md file

## 📊 Using the Dashboard

1. **Look for red/yellow flags** - Low scores need attention
2. **Check seller performance** - See which agents are best
3. **Analyze account history** - Click "View" on any deal to see past sales to that company
4. **Review analytics** - See trends by deal age, company size, product

---

**Ready to prioritize your pipeline? Let's go! 🎯**
