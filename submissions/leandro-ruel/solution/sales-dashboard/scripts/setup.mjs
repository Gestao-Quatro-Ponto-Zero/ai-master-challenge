#!/usr/bin/env node

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(__dirname, '..');

console.log('🚀 Sales Dashboard Setup\n');
console.log('This script will:');
console.log('  1. Install npm dependencies');
console.log('  2. Load data from CSV files into SQLite database');
console.log('  3. Prepare the project for development\n');

// Check if node_modules exists
const nodeModulesPath = path.join(projectRoot, 'node_modules');
const hasNodeModules = fs.existsSync(nodeModulesPath);

async function runCommand(command, args, description) {
  return new Promise((resolve, reject) => {
    console.log(`⏳ ${description}...`);
    const proc = spawn(command, args, {
      cwd: projectRoot,
      stdio: 'inherit',
      shell: process.platform === 'win32'
    });

    proc.on('close', (code) => {
      if (code === 0) {
        console.log(`✅ ${description} completed\n`);
        resolve();
      } else {
        reject(new Error(`${description} failed with code ${code}`));
      }
    });

    proc.on('error', (err) => {
      reject(err);
    });
  });
}

async function setup() {
  try {
    // Install dependencies
    if (!hasNodeModules) {
      await runCommand('npm', ['install'], 'Installing dependencies');
    } else {
      console.log('✅ Dependencies already installed\n');
    }

    // Load data
    await runCommand('node', ['scripts/load-data.mjs'], 'Loading data from CSV files');

    console.log('🎉 Setup completed successfully!\n');
    console.log('Next steps:');
    console.log('  1. Start the development server: npm run dev');
    console.log('  2. In another terminal, start the API server: npm run server');
    console.log('  3. Open http://localhost:5173 in your browser\n');
    console.log('Or run both together: npm start\n');

  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  }
}

setup();
