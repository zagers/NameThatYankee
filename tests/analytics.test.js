import { describe, it, expect, vi, beforeEach } from 'vitest';
import { initAnalytics } from '../js/analytics.js';

// Mock Global/External Dependencies
vi.stubGlobal('firebaseConfig', {});
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-app.js', () => ({ initializeApp: vi.fn() }));
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-app-check.js', () => ({ initializeAppCheck: vi.fn(), ReCaptchaV3Provider: vi.fn() }));
vi.mock('https://www.gstatic.com/firebasejs/12.0.0/firebase-firestore.js', () => ({ getFirestore: vi.fn(), collection: vi.fn(), getDocs: vi.fn(() => ({ docs: [] })) }));

describe('initAnalytics', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="loading-message"></div>
            <div id="analytics-content" class="hidden"></div>
            <canvas id="teamChart"></canvas>
            <canvas id="decadeChart"></canvas>
            <canvas id="guessesChart"></canvas>
            <canvas id="toughestPuzzlesChart"></canvas>
        `;
        vi.clearAllMocks();
    });

    it('should fetch stats_summary.json once', async () => {
        const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation((url) => {
            if (url === 'stats_summary.json') {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve([{ date: '2026-04-18', name: 'Fran Healy', teams: ['NYY'], years: ['1971'] }])
                });
            }
            return Promise.resolve({ ok: true, text: () => Promise.resolve('') });
        });

        await initAnalytics();

        expect(fetchSpy).toHaveBeenCalledWith('stats_summary.json');
        // It should NOT fetch index.html anymore
        const calls = fetchSpy.mock.calls.map(c => c[0]);
        expect(calls).not.toContain('index.html');
    });
});
