// ESLint configuration for SVG Font Analyzer
import js from '@eslint/js';
import eslintPluginImportX from 'eslint-plugin-import-x';
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import tseslint from 'typescript-eslint';

/** @type {import('eslint').Linter.Config[]} */
export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...svelte.configs['flat/recommended'],
  {
    ignores: [
      'node_modules/**/*',
      'dist/**/*',
      '.venv/**/*',
      'uploads/**/*',
      '*.db',
      '*.db-journal',
    ],
  },
  {
    files: ['**/*.js', '**/*.ts'],
    languageOptions: {
      globals: { ...globals.es2021, ...globals.browser },
      parser: tseslint.parser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
  },
  {
    files: ['vite.config.js', 'vite.config.ts', 'eslint.config.js'],
    languageOptions: {
      globals: { ...globals.es2021, ...globals.node },
    },
  },
  {
    files: ['**/*.svelte'],
    languageOptions: {
      globals: { ...globals.es2021, ...globals.browser },
      parserOptions: {
        parser: tseslint.parser,
      },
    },
    rules: {
      'no-inner-declarations': 'off',
      'no-self-assign': 'off',
      'svelte/no-at-html-tags': 'off',
      'svelte/require-each-key': 'off',
      'svelte/valid-compile': ['error', { ignoreWarnings: true }],
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
    },
  },
  {
    plugins: {
      'simple-import-sort': simpleImportSort,
      'import-x': eslintPluginImportX,
    },
    rules: {
      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',
      'import-x/first': 'error',
      'import-x/newline-after-import': 'error',
      'import-x/no-duplicates': 'error',
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },
];
