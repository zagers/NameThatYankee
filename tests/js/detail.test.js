import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { initScoreDisplay } from '../../js/scoreDisplay.js';

describe('detail.js redirect logic', () => {
    let originalLocation;

    beforeEach(async () => {
        vi.resetModules();
        localStorage.clear();
        
        // Mock window.location using Object.defineProperty for stability
        originalLocation = window.location;
        Object.defineProperty(window, 'location', {
            configurable: true,
            value: {
                pathname: '/2026-04-26.html',
                href: 'https://namethatyankeequiz.com/2026-04-26.html',
                search: '',
                origin: 'https://namethatyankeequiz.com',
                replace: vi.fn()
            }
        });

        // Locally mock scoreDisplay for redirect tests
        vi.mock('../../js/scoreDisplay.js', () => ({
            initScoreDisplay: vi.fn()
        }));
    });

    afterEach(() => {
        Object.defineProperty(window, 'location', {
            configurable: true,
            value: originalLocation
        });
        vi.unmock('../../js/scoreDisplay.js');
    });

    it('should redirect to quiz if puzzle is not solved and no reveal flag', async () => {
        // Import triggers immediate handleRedirect()
        await import('../../js/detail.js');
        expect(window.location.replace).toHaveBeenCalledWith('https://namethatyankeequiz.com/quiz?date=2026-04-26');
    });

    it('should handle optional trailing slash in redirect logic', async () => {
        window.location.pathname = '/2026-04-26/';
        window.location.href = 'https://namethatyankeequiz.com/2026-04-26/';
        
        await import('../../js/detail.js');
        expect(window.location.replace).toHaveBeenCalledWith('https://namethatyankeequiz.com/quiz?date=2026-04-26');
    });

    it('should support subdirectory hosting in redirect logic', async () => {
        window.location.pathname = '/yankee/2026-04-26';
        window.location.href = 'https://namethatyankeequiz.com/yankee/2026-04-26';
        
        await import('../../js/detail.js');
        expect(window.location.replace).toHaveBeenCalledWith('https://namethatyankeequiz.com/yankee/quiz?date=2026-04-26');
    });

    it('should NOT redirect if reveal=true flag is present', async () => {
        window.location.search = '?reveal=true';
        await import('../../js/detail.js');
        expect(window.location.replace).not.toHaveBeenCalled();
    });

    it('should NOT redirect if puzzle is already solved', async () => {
        localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(['2026-04-26']));
        await import('../../js/detail.js');
        expect(window.location.replace).not.toHaveBeenCalled();
    });
});

describe('Detail Page Score Display (Restored)', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <header>
                <div class="header-controls">
                    <div id="score-display">
                        Your Score: <span id="total-score">0</span>
                        <div id="score-breakdown-container" style="display: none;">
                            <table>
                                <tbody id="breakdown-body"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </header>
            <main></main>
        `;
        global.localStorage.clear();
    });

    it('should initialize score and breakdown on a detail page', () => {
        localStorage.setItem('nameThatYankeeTotalScore', '17');
        localStorage.setItem('nameThatYankeeScoreBreakdown', JSON.stringify({ "0": 1, "1": 1, "2": 0, "3": 0 }));

        initScoreDisplay();

        expect(document.getElementById('total-score').textContent).toBe('17');
        
        const scoreDisplay = document.getElementById('score-display');
        const breakdownContainer = document.getElementById('score-breakdown-container');
        
        // Toggle open
        scoreDisplay.click();
        expect(breakdownContainer.style.display).toBe('block');
        
        const rows = document.querySelectorAll('#breakdown-body tr');
        expect(rows.length).toBe(4);
        expect(rows[0].textContent).toContain('1'); // 1st clue count
        expect(rows[1].textContent).toContain('1'); // 2nd clue count
    });

    it('should close breakdown when clicking outside', () => {
        initScoreDisplay();
        const scoreDisplay = document.getElementById('score-display');
        const breakdownContainer = document.getElementById('score-breakdown-container');

        scoreDisplay.click(); // Open
        expect(breakdownContainer.style.display).toBe('block');

        // Click main content
        document.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(breakdownContainer.style.display).toBe('none');
    });
});
