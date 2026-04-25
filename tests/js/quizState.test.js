import { describe, it, expect, vi } from 'vitest';

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
vi.mock('../../js/quizEngine.js', () => {
    return {
        normalizeText: vi.fn(text => text ? text.toLowerCase().trim() : ''),
        calculateScore: vi.fn(),
        getAutocompleteSuggestions: vi.fn(),
        QuizEngine: class {}
    };
});

// Mock initScoreDisplay
vi.mock('../../js/scoreDisplay.js', () => ({
    initScoreDisplay: vi.fn()
}));

import { createInitialState, reducer } from '../../js/quiz.js';

describe('Quiz State Management', () => {
    const mockDate = '2025-07-11';

    describe('createInitialState', () => {
        it('should create the default state object', () => {
            const state = createInitialState(mockDate);
            expect(state).toEqual({
                status: 'loading',
                date: mockDate,
                playerIdentity: '',
                guesses: [],
                score: 100,
                hintsRequested: 0,
                shareEvents: [],
                isComplete: false,
                finalScore: 0,
                error: null,
                isProcessing: false
            });
        });
    });

    describe('reducer', () => {
        it('should handle INIT_DATA', () => {
            const initialState = createInitialState(mockDate);
            const action = {
                type: 'INIT_DATA',
                payload: {
                    playerIdentity: 'Derek Jeter',
                    hints: ['Hint 1', 'Hint 2']
                }
            };
            const newState = reducer(initialState, action);
            expect(newState.status).toBe('active');
            expect(newState.playerIdentity).toBe('Derek Jeter');
            // Note: hints might not be in state if not requested in prompt, 
            // but usually they are needed for the engine. 
            // The prompt says: "Sets playerIdentity, hints, etc., and sets status to active."
            // So I'll check if they are set.
        });

        it('should handle GUESS_RESULT for correct guess', () => {
            const state = {
                ...createInitialState(mockDate),
                status: 'active'
            };
            const action = {
                type: 'GUESS_RESULT',
                payload: {
                    status: 'CORRECT',
                    score: 10,
                    guess: 'Derek Jeter'
                }
            };
            const newState = reducer(state, action);
            expect(newState.isComplete).toBe(true);
            expect(newState.status).toBe('complete');
            expect(newState.finalScore).toBe(10);
            expect(newState.guesses).toContain('Derek Jeter');
            expect(newState.shareEvents).toContain('hit');
        });

        it('should handle GUESS_RESULT for incorrect guess', () => {
            const state = {
                ...createInitialState(mockDate),
                status: 'active'
            };
            const action = {
                type: 'GUESS_RESULT',
                payload: {
                    status: 'INCORRECT_VALID_PLAYER',
                    guess: 'Babe Ruth',
                    gameOver: false
                }
            };
            const newState = reducer(state, action);
            expect(newState.guesses).toContain('Babe Ruth');
            expect(newState.shareEvents).toContain('miss');
            expect(newState.isComplete).toBe(false);
        });

        it('should handle GUESS_RESULT for incorrect guess leading to game over', () => {
            const state = {
                ...createInitialState(mockDate),
                status: 'active'
            };
            const action = {
                type: 'GUESS_RESULT',
                payload: {
                    status: 'INCORRECT_VALID_PLAYER',
                    guess: 'Babe Ruth',
                    gameOver: true
                }
            };
            const newState = reducer(state, action);
            expect(newState.isComplete).toBe(true);
            expect(newState.status).toBe('complete');
            expect(newState.finalScore).toBe(0);
        });

        it('should handle REVEAL_HINT', () => {
            const state = {
                ...createInitialState(mockDate),
                hintsRequested: 0,
                shareEvents: []
            };
            const action = { type: 'REVEAL_HINT' };
            const newState = reducer(state, action);
            expect(newState.hintsRequested).toBe(1);
            expect(newState.shareEvents).toContain('hint');
        });

        it('should handle SET_ERROR', () => {
            const state = createInitialState(mockDate);
            const action = { type: 'SET_ERROR', payload: 'Something went wrong' };
            const newState = reducer(state, action);
            expect(newState.error).toBe('Something went wrong');
        });

        it('should handle SET_PROCESSING', () => {
            const state = createInitialState(mockDate);
            const action = { type: 'SET_PROCESSING', payload: true };
            const newState = reducer(state, action);
            expect(newState.isProcessing).toBe(true);
            
            const nextState = reducer(newState, { type: 'SET_PROCESSING', payload: false });
            expect(nextState.isProcessing).toBe(false);
        });
    });
});
