// SSR/hydration-safety lint. Run automatically by the platform after each build:
//   yarn eslint -c eslint.ssr.config.mjs .
// Catches the error class behind most Next.js hydration failures. Do NOT delete or
// weaken this file to silence errors — fix the flagged code (see components/client-only.tsx
// and components/safe-format.tsx for ready-made safe patterns).
import tsParser from '@typescript-eslint/parser'

const BROWSER_GLOBALS = new Set(['window', 'document', 'localStorage', 'sessionStorage', 'navigator'])
const IMPURE_CALLS = { 'Date.now': true, 'Math.random': true }
const LOCALE_METHODS = new Set(['toLocaleDateString', 'toLocaleTimeString', 'toLocaleString'])
const FUNCTION_TYPES = new Set(['FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'])

function isTypeofGuard(node) {
  // `typeof window !== 'undefined'` is a valid SSR guard
  return node.parent?.type === 'UnaryExpression' && node.parent.operator === 'typeof'
}

function isReference(node) {
  const p = node.parent
  if (!p) return false
  if (p.type === 'MemberExpression' && p.property === node && !p.computed) return false
  if (p.type === 'Property' && p.key === node && !p.computed) return false
  if (p.type.startsWith('TS')) return false
  if (p.type.startsWith('Import') || p.type.startsWith('Export')) return false
  if ((p.type === 'VariableDeclarator' && p.id === node) || p.type.includes('Pattern')) return false
  return true
}

const ssrPlugin = {
  rules: {
    'no-browser-globals-in-module-scope': {
      meta: {
        type: 'problem',
        docs: { description: 'Browser globals at module scope crash or mismatch during SSR' },
        schema: [],
      },
      create(context) {
        return {
          Identifier(node) {
            if (!BROWSER_GLOBALS.has(node.name) || !isReference(node) || isTypeofGuard(node)) return
            const inFunction = context.sourceCode.getAncestors(node).some((a) => FUNCTION_TYPES.has(a.type) || a.type === 'ClassBody')
            if (!inFunction) {
              context.report({
                node,
                message: `\`${node.name}\` at module scope runs during SSR where it is undefined. Move it inside useEffect, an event handler, or wrap the UI in <ClientOnly> (components/client-only.tsx).`,
              })
            }
          },
        }
      },
    },
    'no-impure-values-in-render': {
      meta: {
        type: 'problem',
        docs: { description: 'Non-deterministic values in render/state-init cause hydration mismatches' },
        schema: [],
      },
      create(context) {
        function impureName(node) {
          if (node.type === 'NewExpression' && node.callee.type === 'Identifier' && node.callee.name === 'Date' && node.arguments.length === 0) return 'new Date()'
          if (node.type === 'CallExpression' && node.callee.type === 'MemberExpression' && !node.callee.computed && node.callee.object.type === 'Identifier') {
            const name = `${node.callee.object.name}.${node.callee.property.name}`
            if (IMPURE_CALLS[name]) return `${name}()`
          }
          return null
        }
        function check(node) {
          const name = impureName(node)
          if (!name) return
          let crossedFunction = false
          // Walk ancestors innermost-first: hook initializer args always flag (lazy
          // initializers still run during SSR render); direct JSX only flags when no
          // function boundary (e.g. event handler) sits in between.
          for (const anc of context.sourceCode.getAncestors(node).slice().reverse()) {
            if (FUNCTION_TYPES.has(anc.type)) crossedFunction = true
            if (anc.type === 'CallExpression' && anc.callee.type === 'Identifier' && ['useState', 'useReducer', 'useMemo'].includes(anc.callee.name)) {
              context.report({ node, message: `\`${name}\` in ${anc.callee.name}() runs during SSR and again on the client, producing different values (hydration mismatch). Initialize deterministically and update the value inside useEffect, or wrap the UI in <ClientOnly>.` })
              return
            }
            if (anc.type === 'JSXExpressionContainer' && !crossedFunction) {
              context.report({ node, message: `\`${name}\` rendered directly in JSX differs between server and client (hydration mismatch). Compute it in useEffect/state, or use <SafeDate>/<ClientOnly> from components/.` })
              return
            }
          }
        }
        return { CallExpression: check, NewExpression: check }
      },
    },
    'no-bare-locale-format': {
      meta: {
        type: 'problem',
        docs: { description: 'Locale formatting without explicit locale/timeZone differs between server and client' },
        schema: [],
      },
      create(context) {
        return {
          CallExpression(node) {
            if (node.callee.type === 'MemberExpression' && !node.callee.computed && node.callee.property.type === 'Identifier' && LOCALE_METHODS.has(node.callee.property.name) && node.arguments.length === 0) {
              context.report({
                node,
                message: `\`${node.callee.property.name}()\` without arguments uses the runtime's locale/timezone, which differs between server and client (hydration mismatch). Pass an explicit locale (and timeZone for dates), e.g. ('en-US', { timeZone: 'UTC' }), or use <SafeDate>/<SafeTime>/<SafeNumber> from components/safe-format.tsx.`,
              })
            }
          },
        }
      },
    },
  },
}

export default [
  {
    ignores: ['node_modules/**', '.next/**', '.build/**', '.deploy/**', 'out/**', 'dist/**', 'build/**', 'prisma/**', 'scripts/**', '**/*.d.ts', 'next.config.js', 'postcss.config.js', 'tailwind.config.ts'],
  },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: { ecmaFeatures: { jsx: true }, sourceType: 'module' },
    },
    // This pass runs with --no-config-lookup, so plugins from eslint.config.mjs
    // (react-hooks, @typescript-eslint, @next/next, ...) are not visible here and a
    // disable comment naming any of their rules would otherwise hard-fail the run
    // with "Definition for rule ... was not found". Ignoring inline config closes
    // that whole class — and also means the ssr rules themselves cannot be
    // suppressed with disable comments (fix the flagged code instead).
    linterOptions: { noInlineConfig: true },
    plugins: { ssr: ssrPlugin },
    rules: {
      'ssr/no-browser-globals-in-module-scope': 'error',
    },
  },
  {
    files: ['**/*.tsx'],
    rules: {
      'ssr/no-impure-values-in-render': 'error',
      'ssr/no-bare-locale-format': 'error',
    },
  },
]
