import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';

// Mock the Firebase imports
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js', () => ({
    initializeApp: vi.fn()
}));
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-app-check.js', () => ({
    initializeAppCheck: vi.fn(),
    ReCaptchaV3Provider: vi.fn()
}));
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-firestore.js', () => ({
    getFirestore: vi.fn(),
    collection: vi.fn(),
    getDocs: vi.fn(() => Promise.resolve({ docs: [{ data: () => ({ guessText: 'Jeter', puzzleDate: '2025-05-15' }) }] }))
}));

// Mock the analyticsData functions
vi.mock('../../js/analyticsData.js', () => ({
    processTeamData: vi.fn(() => ({ labels: ['NYY'], data: [1] })),
    processDecadeData: vi.fn(() => ({ labels: ['1990s'], data: [1], originalDecades: ['1990'] })),
    processGuessesData: vi.fn(() => ({ labels: ['Jeter'], data: [1] })),
    processToughestPuzzlesData: vi.fn(() => ({ labels: ['May 15, 2025'], data: [1], originalDates: ['2025-05-15'] }))
}));

import { initAnalytics } from '../../js/analytics.js';

describe('Analytics DOM tests', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="loading-message">Loading...</div>
            <div id="analytics-content" class="hidden">
                <div id="total-score">0</div>
                <canvas id="teamChart"></canvas>
                <canvas id="decadeChart"></canvas>
                <canvas id="guessesChart"></canvas>
                <canvas id="toughestPuzzlesChart"></canvas>
            </div>
        `;

        window.firebaseConfig = {}; // Mock global

        // Mock Chart JS
        global.Chart = vi.fn(function (ctx, config) {
            this.ctx = ctx;
            this.config = config;
        });

        // Mock fetch for scraping index.html and puzzle pages
        global.fetch = vi.fn((url) => {
            if (url === 'index.html') {
                return Promise.resolve({
                    text: () => Promise.resolve(`
                        <div class="gallery-item" href="2025-05-15.html"></div>
                    `)
                });
            } else if (url === '2025-05-15.html') {
                return Promise.resolve({
                    text: () => Promise.resolve(`
                        <div id="search-data">{"teams": ["NYY"], "years": [1995, 2000]}</div>
                    `)
                });
            }
            return Promise.resolve({ text: () => Promise.resolve('') });
        });
    });

    it('should initialize and load charts', async () => {
        global.localStorage.setItem('nameThatYankeeTotalScore', '120');

        await initAnalytics();

        // Check that UI was updated
        expect(document.getElementById('total-score').textContent).toBe('120');
        expect(document.getElementById('loading-message').style.display).toBe('none');
        expect(document.getElementById('analytics-content').classList.contains('hidden')).toBe(false);

        // Verify Chart was instantiated 4 times
        expect(global.Chart).toHaveBeenCalledTimes(4);

        // Let's verify standard fetch behavior
        expect(global.fetch).toHaveBeenCalledWith('index.html');
        expect(global.fetch).toHaveBeenCalledWith('2025-05-15.html');
    });

    it('should show error message if fetch fails', async () => {
        global.fetch = vi.fn(() => Promise.reject(new Error("Network Error")));

        await initAnalytics();

        expect(document.getElementById('loading-message').innerHTML).toContain('Could not load analytics data');
    });
});
