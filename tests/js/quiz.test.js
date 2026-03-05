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
        if (guess.toLowerCase() === answer.toLowerCase()) return { status: 'CORRECT' };
        if (guess.toLowerCase() === 'babe ruth') return { status: 'INCORRECT_VALID_PLAYER' };
        return { status: 'INVALID_PLAYER' };
    }),
    calculateScore: vi.fn(() => 10),
    getAutocompleteSuggestions: vi.fn((input) => {
        if (input.toLowerCase() === 'de') return ['Derek Jeter', 'Dennis Rasmussen'];
        return [];
    })
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
        global.localStorage.clear();

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

    it('should handle empty guess submissions', async () => {
        await initQuiz();
        const guessInput = document.getElementById('guess-input');
        const submitBtn = document.getElementById('submit-guess');
        const feedbackMsg = document.getElementById('feedback-message');

        guessInput.value = '   ';
        submitBtn.click();

        expect(feedbackMsg.textContent).toBe('Please enter a valid guess.');
        expect(feedbackMsg.className).toBe('incorrect');
    });

    it('should handle invalid player guess', async () => {
        await initQuiz();
        const guessInput = document.getElementById('guess-input');
        const submitBtn = document.getElementById('submit-guess');
        const feedbackMsg = document.getElementById('feedback-message');

        guessInput.value = 'Not A Real Player';
        submitBtn.click();

        expect(feedbackMsg.textContent).toContain('not a valid MLB player');
        expect(feedbackMsg.className).toBe('incorrect');
    });

    it('should handle incorrect valid player guess and reveal hint', async () => {
        await initQuiz();
        const guessInput = document.getElementById('guess-input');
        const submitBtn = document.getElementById('submit-guess');
        const feedbackMsg = document.getElementById('feedback-message');
        const hintsContainer = document.getElementById('hints-container');
        const hintsList = document.getElementById('hints-list');

        guessInput.value = 'Babe Ruth'; // Triggers INCORRECT_VALID_PLAYER in our mock
        submitBtn.click();

        expect(feedbackMsg.textContent).toBe('Incorrect. Try again!');
        expect(hintsContainer.style.display).toBe('block');
        expect(hintsList.children.length).toBe(1);
        expect(hintsList.children[0].textContent).toBe('Hint 1');
    });

    it('should end quiz if hints are exhausted and incorrect guess is made', async () => {
        await initQuiz();
        const guessInput = document.getElementById('guess-input');
        const submitBtn = document.getElementById('submit-guess');
        const hintBtn = document.getElementById('request-hint');
        const feedbackMsg = document.getElementById('feedback-message');

        // Reveal all hits
        hintBtn.click(); // Hint 1
        hintBtn.click(); // Hint 2
        expect(hintBtn.disabled).toBe(true);
        expect(feedbackMsg.textContent).toContain('All hints revealed! One guess remaining.');

        // Guess wrong again to exhaust quiz
        guessInput.value = 'Babe Ruth';
        submitBtn.click();

        expect(submitBtn.disabled).toBe(true);
        expect(guessInput.disabled).toBe(true);
        expect(feedbackMsg.innerHTML).toContain('Sorry, the correct answer was');
    });

    it('should handle give up button', async () => {
        await initQuiz();
        const giveUpBtn = document.getElementById('give-up-btn');
        const submitBtn = document.getElementById('submit-guess');
        const feedbackMsg = document.getElementById('feedback-message');

        giveUpBtn.click();

        expect(submitBtn.disabled).toBe(true);
        expect(giveUpBtn.disabled).toBe(true);
        expect(feedbackMsg.innerHTML).toContain('Sorry, the correct answer was');
    });

    it('should show autocomplete suggestions', async () => {
        await initQuiz();
        const guessInput = document.getElementById('guess-input');
        const suggestionsContainer = document.getElementById('suggestions-container');

        guessInput.value = 'de';
        guessInput.dispatchEvent(new Event('input'));

        expect(suggestionsContainer.style.display).toBe('block');
        const items = suggestionsContainer.querySelectorAll('.suggestion-item');
        expect(items.length).toBe(2);

        // Click suggestion
        items[0].click();
        expect(guessInput.value).toBe('Derek Jeter');
        expect(suggestionsContainer.style.display).toBe('none');
    });

    it('should keyboard navigate autocomplete suggestions', async () => {
        await initQuiz();
        const guessInput = document.getElementById('guess-input');
        const suggestionsContainer = document.getElementById('suggestions-container');

        guessInput.value = 'de';
        guessInput.dispatchEvent(new Event('input')); // Generate suggestions

        // Arrow down
        const arrowDownEvent = new window.KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true });
        guessInput.dispatchEvent(arrowDownEvent);

        const items = suggestionsContainer.querySelectorAll('.suggestion-item');
        expect(items[0].classList.contains('highlighted')).toBe(true);

        // Arrow down again
        guessInput.dispatchEvent(arrowDownEvent);
        expect(items[0].classList.contains('highlighted')).toBe(false);
        expect(items[1].classList.contains('highlighted')).toBe(true);

        // Arrow up
        const arrowUpEvent = new window.KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true });
        guessInput.dispatchEvent(arrowUpEvent);
        expect(items[0].classList.contains('highlighted')).toBe(true);

        // Enter should submit Highlighted Item
        const enterEvent = new window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
        guessInput.dispatchEvent(enterEvent);

        // The mock logic will handle this as CORRECT
        expect(document.getElementById('success-area').style.display).toBe('block');
    });
});
