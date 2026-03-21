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
    addDoc: vi.fn(),
    query: vi.fn(),
    where: vi.fn(),
    getDocs: vi.fn(),
    serverTimestamp: vi.fn(),
    doc: vi.fn(),
    getDoc: vi.fn(),
    setDoc: vi.fn()
}));

// Mock the quizEngine imports
vi.mock('../../js/quizEngine.js', () => ({
    normalizeText: vi.fn(),
    validateGuess: vi.fn((guess, answer) => {
        if (guess.toLowerCase() === answer.toLowerCase()) return { status: 'CORRECT' };
        return { status: 'INCORRECT_VALID_PLAYER' };
    }),
    calculateScore: vi.fn((hints) => [10, 7, 4, 1, 0][hints]),
    getAutocompleteSuggestions: vi.fn(() => [])
}));

import { initQuiz } from '../../js/quiz.js';
import { initIndex } from '../../js/index.js';

describe('Score Breakdown Feature', () => {
    
    describe('Quiz Logic - Recording Breakdown', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <h1 id="quiz-title"></h1>
                <div class="header-controls">
                    <div id="score-display">
                        Your Score: <span id="total-score">0</span>
                        <svg class="chevron-icon"></svg>
                        <div id="score-breakdown-container" style="display: none;">
                            <table>
                                <tbody id="breakdown-body"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <div id="quiz-area">
                    <img id="clue-image" />
                    <div id="suggestions-container"></div>
                    <input id="guess-input" />
                    <button id="submit-guess"></button>
                    <button id="request-hint"></button>
                    <button id="give-up-btn"></button>
                    <div id="feedback-message"></div>
                    <div id="share-fail-container" style="display: none;">
                        <button id="share-btn-fail"></button>
                    </div>
                    <div id="hints-container" style="display: none;"><ul id="hints-list"></ul></div>
                    <button id="show-guesses-btn"></button>
                    </div>
                    <div id="success-area" style="display: none;">
                    <img id="answer-image" />
                    <h2 id="success-header"></h2>
                    <div id="success-points">0</div>
                    <div class="success-actions">
                        <button id="share-btn-success"></button>
                        <a id="view-answer-link"></a>
                    </div>
                    </div>
                    <div id="total-score">0</div>
                    <div id="guesses-chart-container"><canvas id="guessesChart"></canvas></div>
                    `;
                    global.localStorage.clear();
                    window.firebaseConfig = {};
                    delete window.location;
                    window.location = new URL('http://localhost/quiz.html?date=2026-03-20');
                    window.location.assign = vi.fn(); // Mock assign to avoid relative URL issues if any

                    global.fetch = vi.fn().mockImplementation(() => Promise.resolve({
                    text: () => Promise.resolve('<div id="quiz-data">{"answer": "Bernie Williams", "hints": ["Hint 1", "Hint 2", "Hint 3", "Hint 4"]}</div>')
                    }));        });

        it('should record breakdown for 0 hints used (10pts)', async () => {
            await initQuiz();
            const guessInput = document.getElementById('guess-input');
            const submitBtn = document.getElementById('submit-guess');

            guessInput.value = 'Bernie Williams';
            submitBtn.click();

            const breakdown = JSON.parse(localStorage.getItem('nameThatYankeeScoreBreakdown'));
            expect(breakdown).not.toBeNull();
            expect(breakdown["0"]).toBe(1);
            expect(breakdown["1"]).toBe(0);
        });

        it('should record breakdown for 1 hint used (7pts)', async () => {
            await initQuiz();
            const guessInput = document.getElementById('guess-input');
            const submitBtn = document.getElementById('submit-guess');
            const hintBtn = document.getElementById('request-hint');

            hintBtn.click(); // 1 hint used
            guessInput.value = 'Bernie Williams';
            submitBtn.click();

            const breakdown = JSON.parse(localStorage.getItem('nameThatYankeeScoreBreakdown'));
            expect(breakdown["1"]).toBe(1);
            expect(breakdown["0"]).toBe(0);
        });

        it('should increment counts correctly across multiple games', async () => {
            // Mock a win with 2 hints already in storage
            localStorage.setItem('nameThatYankeeScoreBreakdown', JSON.stringify({ "0": 2, "1": 5, "2": 0, "3": 0 }));
            
            await initQuiz();
            const guessInput = document.getElementById('guess-input');
            const submitBtn = document.getElementById('submit-guess');
            const hintBtn = document.getElementById('request-hint');

            hintBtn.click();
            hintBtn.click(); // 2 hints used
            guessInput.value = 'Bernie Williams';
            submitBtn.click();

            const breakdown = JSON.parse(localStorage.getItem('nameThatYankeeScoreBreakdown'));
            expect(breakdown["2"]).toBe(1);
            expect(breakdown["0"]).toBe(2);
            expect(breakdown["1"]).toBe(5);
        });

        it('should clear breakdown when reset=true is passed', async () => {
            localStorage.setItem('nameThatYankeeScoreBreakdown', JSON.stringify({ "0": 2, "1": 5, "2": 0, "3": 0 }));
            delete window.location;
            window.location = new URL('http://localhost/quiz.html?reset=true');
            window.location.assign = vi.fn(); 
            window.alert = vi.fn(); // Mock alert

            await initQuiz();

            expect(localStorage.getItem('nameThatYankeeScoreBreakdown')).toBeNull();
        });

        it('should allow toggling breakdown UI during an active quiz session', async () => {
            localStorage.setItem('nameThatYankeeScoreBreakdown', JSON.stringify({ "0": 5, "1": 2, "2": 0, "3": 0 }));
            
            await initQuiz();
            const scoreDisplay = document.getElementById('score-display');
            const breakdownContainer = document.getElementById('score-breakdown-container');
            const breakdownBody = document.getElementById('breakdown-body');

            expect(breakdownContainer.style.display).toBe('none');

            scoreDisplay.click();
            expect(breakdownContainer.style.display).toBe('block');
            expect(breakdownBody.querySelectorAll('tr')[0].textContent).toContain('5');
        });
    });

    describe('Index UI - Displaying Breakdown', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <div class="header-controls">
                    <div id="score-display">
                        Your Score: <span id="total-score">0</span>
                        <svg class="chevron-icon"></svg>
                        <div id="score-breakdown-container" style="display: none;">
                            <table>
                                <tbody id="breakdown-body"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <input id="search-bar" type="text" />
                <input type="checkbox" id="unsolved-filter" />
                <div id="gallery-grid"></div>
                <div id="no-results" style="display: none;"></div>
                <button id="share-btn-success"></button>
                <button id="share-btn-fail"></button>
            `;
            global.localStorage.clear();
            window.firebaseConfig = {};
            delete window.location;
            window.location = new URL('http://localhost/index.html');
        });

        it('should toggle breakdown visibility when clicking score display', async () => {
            await initIndex();
            const scoreDisplay = document.getElementById('score-display');
            const breakdownContainer = document.getElementById('score-breakdown-container');

            expect(breakdownContainer.style.display).toBe('none');

            scoreDisplay.click();
            expect(breakdownContainer.style.display).toBe('block');

            scoreDisplay.click();
            expect(breakdownContainer.style.display).toBe('none');
        });

        it('should populate breakdown table with data from localStorage', async () => {
            const mockBreakdown = { "0": 1, "1": 2, "2": 3, "3": 4 };
            localStorage.setItem('nameThatYankeeScoreBreakdown', JSON.stringify(mockBreakdown));
            localStorage.setItem('nameThatYankeeTotalScore', '40'); // (1*10 + 2*7 + 3*4 + 4*1) = 40. 

            await initIndex();
            const scoreDisplay = document.getElementById('score-display');
            scoreDisplay.click(); // Trigger population

            const breakdownBody = document.getElementById('breakdown-body');
            
            // Check counts in the table (assuming specific order or IDs in implementation)
            const rows = breakdownBody.querySelectorAll('tr');
            expect(rows.length).toBe(4);
            
            // Row 0 (10 pts) should have count 1
            expect(rows[0].textContent).toContain('1');
            // Row 1 (7 pts) should have count 2
            expect(rows[1].textContent).toContain('2');
        });
    });

    describe('Score Pill Visual Affordance', () => {
        beforeEach(() => {
            document.body.innerHTML = `
                <div class="header-controls">
                    <div id="score-display">
                        Your Score: <span id="total-score">0</span>
                        <svg class="chevron-icon"></svg>
                        <div id="score-breakdown-container" style="display: none;">
                            <table>
                                <tbody id="breakdown-body"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
                <input id="search-bar" type="text" />
                <input type="checkbox" id="unsolved-filter" />
                <div id="gallery-grid"></div>
                <div id="no-results" style="display: none;"></div>
            `;
            global.localStorage.clear();
            window.firebaseConfig = {};
        });

        it('should have a title attribute for accessibility', async () => {
            await initIndex();
            const scoreDisplay = document.getElementById('score-display');
            expect(scoreDisplay.getAttribute('title')).toBe('Click to view score breakdown');
        });

        it('should contain a chevron icon', async () => {
            await initIndex();
            const scoreDisplay = document.getElementById('score-display');
            const chevron = scoreDisplay.querySelector('svg.chevron-icon');
            expect(chevron).not.toBeNull();
        });

        it('should toggle is-active class when clicked', async () => {
            await initIndex();
            const scoreDisplay = document.getElementById('score-display');
            
            expect(scoreDisplay.classList.contains('is-active')).toBe(false);
            
            scoreDisplay.click();
            expect(scoreDisplay.classList.contains('is-active')).toBe(true);
            
            scoreDisplay.click();
            expect(scoreDisplay.classList.contains('is-active')).toBe(false);
        });

        it('should remove is-active class when clicking outside', async () => {
            await initIndex();
            const scoreDisplay = document.getElementById('score-display');
            
            scoreDisplay.click();
            expect(scoreDisplay.classList.contains('is-active')).toBe(true);
            
            // Click outside
            document.body.click();
            expect(scoreDisplay.classList.contains('is-active')).toBe(false);
        });
    });

    it('should toggle is-active class on Enter or Space key press', async () => {
        await initIndex();
        const scoreDisplay = document.getElementById('score-display');
        
        expect(scoreDisplay.classList.contains('is-active')).toBe(false);
        
        const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' });
        scoreDisplay.dispatchEvent(enterEvent);
        expect(scoreDisplay.classList.contains('is-active')).toBe(true);
        
        const spaceEvent = new KeyboardEvent('keydown', { key: ' ' });
        scoreDisplay.dispatchEvent(spaceEvent);
        expect(scoreDisplay.classList.contains('is-active')).toBe(false);
    });
});
