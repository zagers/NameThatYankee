// ABOUTME: Unit tests for Quiz state management.
// ABOUTME: Verifies state transitions and logic using the reducer pattern.

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

import { createInitialState, reducer } from '../../js/quiz.js';

describe('Quiz State Management', () => {
    const mockDate = '2025-07-11';

    describe('createInitialState', () => {
        it('should create the default state object', () => {
            const state = createInitialState(mockDate);
            expect(state.status).toBe('loading');
            expect(state.date).toBe(mockDate);
            expect(state.playerIdentity).toBe('');
            expect(state.guesses).toEqual([]);
            expect(state.score).toBe(100);
            expect(state.hintsRequested).toBe(0);
            expect(state.shareEvents).toEqual([]);
            expect(state.isComplete).toBe(false);
            expect(state.finalScore).toBe(0);
            expect(state.error).toBeNull();
            expect(state.isProcessing).toBe(false);
        });
    });

    describe('reducer', () => {
        it('should handle INIT_DATA', () => {
            const initialState = createInitialState(mockDate);
            const action = {
                type: 'INIT_DATA',
                payload: { playerIdentity: 'Derek Jeter' }
            };
            const nextState = reducer(initialState, action);
            expect(nextState.status).toBe('active');
            expect(nextState.playerIdentity).toBe('Derek Jeter');
        });

        it('should handle CORRECT guess result', () => {
            const state = { ...createInitialState(mockDate), status: 'active' };
            const action = {
                type: 'GUESS_RESULT',
                payload: { status: 'CORRECT', score: 100, guess: 'Derek Jeter', gameOver: true }
            };
            const nextState = reducer(state, action);
            expect(nextState.status).toBe('complete');
            expect(nextState.isComplete).toBe(true);
            expect(nextState.finalScore).toBe(100);
            expect(nextState.guesses).toContain('Derek Jeter');
            expect(nextState.shareEvents).toContain('hit');
        });

        it('should handle INCORRECT valid player guess result', () => {
            const state = { ...createInitialState(mockDate), status: 'active' };
            const action = {
                type: 'GUESS_RESULT',
                payload: { status: 'INCORRECT_VALID_PLAYER', score: 0, guess: 'Aaron Judge', gameOver: false }
            };
            const nextState = reducer(state, action);
            expect(nextState.guesses).toContain('Aaron Judge');
            expect(nextState.shareEvents).toContain('miss');
            expect(nextState.isComplete).toBe(false);
        });

        it('should handle REVEAL_HINT', () => {
            const state = createInitialState(mockDate);
            const action = { type: 'REVEAL_HINT' };
            const nextState = reducer(state, action);
            expect(nextState.hintsRequested).toBe(1);
            expect(nextState.shareEvents).toContain('hint');
        });
    });
});
