import eslintJs from '@eslint/js'
import solidPlugin from 'eslint-plugin-solid'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  // 1. Global ignores
  { ignores: ['dist/', 'dev-dist/', 'node_modules/', 'test-results/', 'playwright-report/'] },

  // 2. Base ESLint recommended rules (applies globally)
  eslintJs.configs.recommended,

  // 3. Configuration for TypeScript Source Files (src/**)
  //    Applies TS Recommended, Type-Checked, Solid Rules + Parser Options
  {
    files: ['src/**/*.{ts,tsx}'],
    // Use 'extends' to apply multiple configs specifically to these files
    extends: [
      ...tseslint.configs.recommended, // Base TS rules
      ...tseslint.configs.strictTypeChecked, // Type-aware rules (strict)
      solidPlugin.configs['flat/typescript'], // Solid rules
    ],
    languageOptions: {
      parserOptions: {
        project: './tsconfig.app.json', // TS project for type-aware rules in 'extends'
        tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.browser, // Browser globals for src files
      },
    },
    // Add specific rule overrides for TS/Solid files here if needed
    rules: {
      // Loosen some strict type checks
      '@typescript-eslint/ban-ts-comment': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-non-null-assertion': 'off',
      '@typescript-eslint/no-unsafe-argument': 'warn',
      '@typescript-eslint/no-unsafe-assignment': 'warn',
      '@typescript-eslint/no-unsafe-call': 'warn',
      '@typescript-eslint/no-unsafe-member-access': 'warn',
      '@typescript-eslint/no-unsafe-return': 'warn',
    },
  },

  // 4. Configuration for Project Root Config Files (*.js, *.cjs)
  {
    files: ['eslint.config.js', '*.cjs'],
    languageOptions: {
      globals: {
        ...globals.node, // Node globals for config files
      },
    },
  },

  // 4b. Vite / Vitest TypeScript config files
  {
    files: ['vite.config.ts', 'vitest.config.ts'],
    extends: [...tseslint.configs.recommended],
    languageOptions: {
      parserOptions: {
        project: './tsconfig.node.json',
        tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.node,
      },
    },
  },

  // 5. Playwright end-to-end tests and config (run in Node; callbacks run in the browser)
  {
    files: ['e2e/**/*.ts', 'playwright.config.ts'],
    extends: [...tseslint.configs.recommended],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  }
)
