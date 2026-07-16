#!/usr/bin/env node

/**
 * Script de contournement pour exécuter ESLint
 * Workaround script to run ESLint
 */

const { execSync } = require('child_process');
const path = require('path');

try {
  // Exécuter ESLint directement
  console.log('🔍 Exécution de ESLint...\n');
  
  // ESLint 9 utilise eslint.config.mjs par défaut
  const result = execSync(
    'npx eslint . --ext .js,.jsx,.ts,.tsx --max-warnings 0',
    {
      cwd: path.resolve(__dirname),
      stdio: 'inherit',
      encoding: 'utf-8'
    }
  );
  
  console.log('\n✅ ESLint terminé avec succès!');
  process.exit(0);
} catch (error) {
  console.error('\n❌ Erreurs ESLint détectées');
  process.exit(1);
}
