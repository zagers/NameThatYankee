import { describe, it, expect, vi, beforeEach } from 'vitest';
import { initScoreDisplay } from '../../js/scoreDisplay.js';

describe('Detail Page Score Display', () => {
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
