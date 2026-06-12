# Troubleshooting Guide

## Common Issues & Solutions

### 🔴 "npm: command not found"

**Problem:** Terminal doesn't recognize `npm` command

**Solution:**
1. Download Node.js from https://nodejs.org/
2. Choose the LTS (Long Term Support) version
3. Install it - make sure to select "Add to PATH" during installation
4. Restart your terminal
5. Type `npm --version` to verify installation

---

### 🔴 "Port 5173 already in use"

**Problem:** Dev server won't start because port is busy

**Solution Option 1 - Quick Fix:**
1. Wait a minute and try again
2. The process might still be running from before

**Solution Option 2 - Change Port:**
1. Open `vite.config.js`
2. Find: `port: 5173`
3. Change to: `port: 5174` (or any number 5000-5999)
4. Save and try again
5. Open: `http://localhost:5174`

**Solution Option 3 - Find What's Using It:**

**Windows:**
```
netstat -ano | findstr :5173
taskkill /PID [PID] /F
```

**Mac/Linux:**
```
lsof -i :5173
kill -9 [PID]
```

---

### 🔴 "Port 3001 already in use"

**Problem:** API server won't start because port is busy

**Solution:**
1. Open `server/api.mjs`
2. Find: `const PORT = 3001;`
3. Change to: `const PORT = 3002;` (or any number)
4. Save and try again

---

### 🔴 "Cannot find module 'better-sqlite3'"

**Problem:** SQLite driver not installed

**Solution:**
```
npm install
```

Then try:
```
npm run setup
```

If still failing:
1. Delete `node_modules` folder
2. Delete `package-lock.json` file
3. Run: `npm install`
4. Run: `npm run setup`

---

### 🔴 "Database not found" or "Database is locked"

**Problem:** SQLite database missing or corrupted

**Solution:**
1. Delete the `data/` folder
2. Run: `npm run setup`
3. This will recreate the database and reload data

---

### 🔴 "Blank page" or "No data showing"

**Problem:** Dashboard loads but no deals visible

**Solution 1 - Refresh:**
- Press `F5` in browser to refresh
- Try `Ctrl+Shift+R` (hard refresh)
- Close and reopen browser tab

**Solution 2 - Check Servers:**
- Make sure API server is running
- Terminal should show: `🚀 API Server running at http://localhost:3001`
- Make sure dev server is running
- Terminal should show: `VITE v...`

**Solution 3 - Check Browser Console:**
1. Press `F12` to open Developer Tools
2. Click "Console" tab
3. Look for red error messages
4. Screenshot the error and contact support

---

### 🔴 "API connection error" or "Failed to fetch"

**Problem:** Dashboard can't connect to API server

**Solution:**
1. Check if API server is running in a terminal window
2. Should show: `🚀 API Server running at http://localhost:3001`
3. If not, run: `npm run server`
4. Refresh your browser (F5)

If still failing:
1. Edit `src/api/client.js`
2. Change: `const API_BASE = 'http://localhost:3001';`
3. To: `const API_BASE = 'http://localhost:3002';` (if you changed the port)
4. Save and refresh browser

---

### 🔴 Setup script fails with errors

**Problem:** `npm run setup` stops with error messages

**Solution 1 - Check for CSV Files:**
1. Navigate to parent folder: `../solution/dataset/`
2. Verify these files exist:
   - `sales_pipeline.csv`
   - `accounts.csv`
   - `products.csv`
   - `sales_teams.csv`
   - `metadata.csv`

**Solution 2 - Clear and Retry:**
```
rm -rf node_modules package-lock.json data/
npm install
npm run setup
```

**Solution 3 - Manual Setup:**
```
npm install
node scripts/load-data.mjs
```

---

### 🔴 Dashboard is very slow

**Problem:** Dashboard takes long to load or filters are sluggish

**Solution 1 - Clear Browser Cache:**
1. Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
2. Select "All time"
3. Check "Cached images and files"
4. Click "Clear"

**Solution 2 - Restart Servers:**
1. Stop both terminals (Ctrl+C)
2. Wait 5 seconds
3. Start again: `npm start`

**Solution 3 - Check System Resources:**
- Close other applications using memory
- Check CPU/Memory usage in Task Manager (Windows) or Activity Monitor (Mac)

---

### 🔴 Filters aren't working

**Problem:** Selecting filters doesn't update the deal list

**Solution 1 - Refresh Data:**
1. Click "Reset" button to clear all filters
2. Click refresh icon (looks like circular arrow)
3. Wait a moment for data to reload

**Solution 2 - Check Browser Console:**
1. Press `F12`
2. Go to "Console" tab
3. Look for error messages in red
4. Take screenshot of error

**Solution 3 - Try Different Filter:**
- If one filter doesn't work, try another
- Some combinations might have no results

---

### 🔴 Score details won't open

**Problem:** Clicking on score badge doesn't show breakdown

**Solution 1 - Try Different Deal:**
- Click on a different deal's score
- Some deals might have missing data

**Solution 2 - Check Browser Console:**
- Press `F12`
- Go to "Console" tab
- Look for errors
- Try opening Developer Tools before clicking score

**Solution 3 - Full Page Refresh:**
- Press `Ctrl+Shift+R` (hard refresh)
- Try clicking score again

---

### 🔴 Windows batch files won't run

**Problem:** `setup.bat` or `start.bat` files don't execute

**Solution 1 - Use PowerShell:**
```
powershell -ExecutionPolicy Bypass -File setup.bat
```

**Solution 2 - Run Manually:**
1. Open Command Prompt in folder
2. Type: `npm install`
3. Type: `npm run setup`
4. Type: `npm start`

**Solution 3 - File Association:**
1. Right-click `.bat` file
2. Select "Open with" → "Command Prompt"
3. Check "Always use this app"

---

### 🔴 Data not updating after CSV change

**Problem:** You updated CSV files but dashboard shows old data

**Solution:**
1. Stop both servers (Ctrl+C)
2. Delete `data/sales.db` file
3. Run: `npm run setup`
4. Run: `npm start`

---

### 🔴 "EADDRINUSE" error

**Problem:** Port is already in use

**Solution 1:**
- Wait 30 seconds and try again
- Port might still be blocked from previous session

**Solution 2:**
- Kill all Node processes:

**Windows:**
```
taskkill /F /IM node.exe
```

**Mac/Linux:**
```
killall node
```

**Solution 3:**
- Change ports in config files as described above

---

### 🔴 Mac: "Permission denied" on shell scripts

**Problem:** `.sh` files won't execute on Mac

**Solution:**
```bash
chmod +x setup.sh
chmod +x start.sh
./setup.sh
```

---

### 🔴 Charts not showing

**Problem:** Analytics tab shows blank where charts should be

**Solution 1 - Wait for Data:**
- Charts load after dashboard data loads
- Can take 5-10 seconds on first load

**Solution 2 - Refresh Page:**
- Press `F5` to refresh
- Try again

**Solution 3 - Check Console:**
- Press `F12` → "Console" tab
- Look for error messages related to Recharts
- Screenshot error and contact support

---

### 🔴 Getting "SSL certificate error"

**Problem:** Browser shows security warning

**Solution:**
- This shouldn't happen on `localhost`
- If it does:
  1. Press Advanced
  2. Click "Proceed anyway"
  3. This is safe for local development

---

### 🔴 Email/Support Access Issues

**Problem:** Links in dashboard show errors

**Solution:**
- This is a local tool - there are no external links
- All data is stored locally
- No internet connection needed (except for initial npm install)

---

## Getting Help

### Before Contacting Support:

1. **Check all this file** - your issue might be listed
2. **Restart services:**
   ```
   Ctrl+C in all terminals
   npm install
   npm run setup
   npm start
   ```
3. **Clear everything and restart:**
   - Delete `node_modules`, `package-lock.json`, `data/`
   - Follow setup steps again

### When Contacting Support, Include:

- **Error message** (copy exactly)
- **Operating system** (Windows/Mac/Linux)
- **Node version**: `node --version`
- **Browser used** (Chrome/Firefox/Safari)
- **Steps you took** before the error
- **Screenshot** of error message

---

## Quick Checklist

Before assuming there's a problem:

- [ ] Both servers running in separate terminals?
- [ ] Port 5173 and 3001 available?
- [ ] Node.js installed? (`node --version`)
- [ ] Dependencies installed? (`npm install`)
- [ ] Data loaded? (`npm run setup`)
- [ ] Browser refreshed? (`F5`)
- [ ] Localhost URL correct? (`http://localhost:5173`)
- [ ] Checked browser console? (`F12`)

---

## Performance Tips

### To make dashboard faster:

1. **Close browser tabs** you're not using
2. **Close other applications** to free up RAM
3. **Use Chrome** (fastest browser for most tasks)
4. **Clear browser cache** regularly
5. **Don't filter** too much (try broader filters first)
6. **Refresh** if sluggish for more than 30 seconds

### To make setup faster:

1. **Good internet connection** for npm install
2. **Close antivirus** temporarily during install
3. **Use SSD** not external drive
4. **Run as administrator** (Windows)

---

## Still Need Help?

### Collect Debug Information:

1. Open Terminal in dashboard folder
2. Run:
```bash
node --version
npm --version
npm list better-sqlite3
npm list express
```
3. Screenshot the output
4. Include in support request

### Check Logs:

Look at terminal output where servers are running:
- Red text = errors
- Yellow text = warnings
- No output = check if process is running

---

**Remember:** Most issues are resolved by restarting the servers. When in doubt, try that first! 🔄

