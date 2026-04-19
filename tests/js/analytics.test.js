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
                <div id="score-display">
                    Your Score: <span id="total-score">0</span>
                    <div id="score-breakdown-container" style="display: none;">
                        <table>
                            <tbody id="breakdown-body"></tbody>
                        </table>
                    </div>
                </div>
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

        // Mock fetch for statistics summary
        global.fetch = vi.fn((url) => {
            if (url === 'stats_summary.json') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([
                        { teams: ["NYY"], years: [1995, 2000], date: '2025-05-15', name: 'Derek Jeter' }
                    ])
                });
            }
            return Promise.resolve({ ok: true, text: () => Promise.resolve('') });
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
        expect(global.fetch).toHaveBeenCalledWith('stats_summary.json');
    });

    it('should show error message if fetch fails', async () => {
        global.fetch = vi.fn(() => Promise.reject(new Error("Network Error")));

        await initAnalytics();

        expect(document.getElementById('loading-message').innerHTML).toContain('Could not load analytics data');
    });
});
