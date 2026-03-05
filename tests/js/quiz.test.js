import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';

// Mock the Firebase imports BEFORE importing quiz.js
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
        return { status: guess.toLowerCase() === answer.toLowerCase() ? 'CORRECT' : 'INVALID_PLAYER' };
    }),
    calculateScore: vi.fn(() => 10),
    getAutocompleteSuggestions: vi.fn(() => [])
}));

import { initQuiz } from '../../js/quiz.js';

describe('Quiz DOM tests', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <h1 id="quiz-title"></h1>
            <div id="quiz-area">
                <img id="clue-image" />
                <input id="guess-input" />
                <button id="submit-guess"></button>
                <button id="request-hint"></button>
                <button id="give-up-btn"></button>
                <div id="feedback-message"></div>
                <div id="hints-container" style="display: none;">
                    <ul id="hints-list"></ul>
                </div>
                <button id="show-guesses-btn"></button>
            </div>
            <div id="success-area" style="display: none;">
                <img id="answer-image" />
                <h2 id="success-header"></h2>
                <div id="success-points"></div>
                <a id="view-answer-link"></a>
            </div>
            <div id="total-score">0</div>
            <div id="guesses-chart-container">
                <canvas id="guessesChart"></canvas>
            </div>
            <div id="suggestions-container" style="display: none;"></div>
        `;

        window.firebaseConfig = {}; // Mock global

        // Setup simple DOM properties that jsdom might miss or we need to override
        delete window.location;
        window.location = new URL('http://localhost/quiz.html?date=2025-07-11');

        // Mock fetch
        global.fetch = vi.fn((url) => {
            if (url.endsWith('.html')) {
                return Promise.resolve({
                    text: () => Promise.resolve('<div id="quiz-data">{"answer": "Derek Jeter", "hints": ["Hint 1", "Hint 2"]}</div>')
                });
            }
            return Promise.resolve({});
        });
    });

    it('should initialize quiz data and set the clue image', async () => {
        await initQuiz();

        expect(document.getElementById('clue-image').src).toContain('images/clue-2025-07-11.webp');
        expect(document.getElementById('quiz-title').textContent).toBe('Quiz for July 11, 2025');
    });

    it('should submit a correct guess and show success area', async () => {
        await initQuiz();

        const guessInput = document.getElementById('guess-input');
        const submitBtn = document.getElementById('submit-guess');

        guessInput.value = 'Derek Jeter';
        submitBtn.click();

        expect(document.getElementById('quiz-area').style.display).toBe('none');
        expect(document.getElementById('success-area').style.display).toBe('block');
        expect(document.getElementById('success-header').textContent).toContain('Derek Jeter');
    });
});
