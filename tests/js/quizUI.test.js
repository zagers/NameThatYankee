// ABOUTME: Tests for the QuizUI renderer.
// ABOUTME: Verifies that the DOM is correctly updated based on the QuizState.

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { QuizUI } from '../../js/quizUI.js';

describe('QuizUI', () => {
    let ui;
    const clues = ['Hint 1', 'Hint 2', 'Hint 3'];

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="quiz-area"></div>
            <div id="success-area" style="display: none;"></div>
            <p id="feedback-message"></p>
            <div id="hints-container" style="display: none;">
                <ul id="hints-list"></ul>
            </div>
            <input id="guess-input">
            <button id="submit-guess">Submit</button>
            <button id="request-hint">Hint</button>
            <button id="give-up-btn">Give Up</button>
            <span id="total-score">0</span>
            <h2 id="success-header"></h2>
            <p id="success-points"></p>
            <div id="share-fail-container" style="display: none;"></div>
        `;
        ui = new QuizUI(clues);
    });

    it('should show success area and correct name when status is solved', () => {
        ui.render({ 
            status: 'complete', 
            playerIdentity: 'Derek Jeter',
            hintsRequested: 0,
            isComplete: true,
            finalScore: 100,
            totalScore: 10
        });
        expect(document.getElementById('quiz-area').style.display).toBe('none');
        expect(document.getElementById('success-area').style.display).not.toBe('none');
        expect(document.getElementById('success-header').textContent).toContain('Derek Jeter');
    });

    it('should show quiz area and hide success area when status is active', () => {
        ui.render({ 
            status: 'active',
            hintsRequested: 0,
            isComplete: false,
            totalScore: 10
        });
        expect(document.getElementById('quiz-area').style.display).not.toBe('none');
        expect(document.getElementById('success-area').style.display).toBe('none');
    });

    it('should display error message when state.error is present', () => {
        ui.render({ 
            error: 'Invalid Player',
            status: 'active',
            hintsRequested: 0
        });
        const feedback = document.getElementById('feedback-message');
        expect(feedback.textContent).toBe('Invalid Player');
    });

    it('should display feedback message when state.feedback is present', () => {
        ui.render({ 
            feedback: 'Nice try!',
            status: 'active',
            hintsRequested: 0
        });
        const feedback = document.getElementById('feedback-message');
        expect(feedback.textContent).toBe('Nice try!');
    });

    it('should append hints based on state.hintsRequested', () => {
        ui.render({ 
            hintsRequested: 2,
            status: 'active'
        });
        const hintsList = document.getElementById('hints-list');
        const hintsContainer = document.getElementById('hints-container');
        expect(hintsContainer.style.display).toBe('block');
        expect(hintsList.children.length).toBe(2);
        expect(hintsList.children[0].textContent).toBe('Hint 1');
        expect(hintsList.children[1].textContent).toBe('Hint 2');
    });

    it('should disable inputs and buttons when isProcessing is true', () => {
        ui.render({ 
            isProcessing: true,
            status: 'active',
            hintsRequested: 0
        });
        expect(document.getElementById('guess-input').disabled).toBe(true);
        expect(document.getElementById('submit-guess').disabled).toBe(true);
        expect(document.getElementById('request-hint').disabled).toBe(true);
        expect(document.getElementById('give-up-btn').disabled).toBe(true);
    });

    it('should prevent XSS by using textContent for dynamic data', () => {
        const maliciousInput = '<img src=x onerror=alert(1)>';
        ui.render({ 
            status: 'complete',
            playerIdentity: maliciousInput,
            isComplete: true,
            finalScore: 100,
            hintsRequested: 0
        });
        expect(document.getElementById('success-header').textContent).toContain(maliciousInput);
        expect(document.getElementById('success-header').innerHTML).not.toContain('<img');
    });
});
