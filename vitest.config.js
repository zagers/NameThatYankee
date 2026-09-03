// ABOUTME: Configuration for Vitest frontend testing framework.
// ABOUTME: Sets up JSDOM and test coverage reporting for JavaScript modules.

import { defineConfig } from 'vitest/config';

export default defineConfig({
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./tests/js/setup.js'],
        include: ['tests/**/*.{test,spec}.?(c|m)[jt]s?(x)'],
        exclude: ['**/node_modules/**', '**/node_modules.nosync/**', '**/.git/**'],
        coverage: {
            provider: 'v8',
            reporter: ['text', 'html'],
            exclude: ['node_modules/', 'tests/']
        }
    }
});
