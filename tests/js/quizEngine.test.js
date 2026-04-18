import { describe, it, expect, beforeEach } from 'vitest';
import { QuizEngine } from '../../js/quizEngine.js';

describe('QuizEngine', () => {
    let engine;
    const answer = "Derek Jeter";
    const clues = ["Clue 1", "Clue 2", "Clue 3"];

    beforeEach(() => {
        engine = new QuizEngine(answer, clues);
    });

    describe('Normalization', () => {
        it('should normalize casing and diacritics', () => {
            expect(engine.normalize("Déreck Jétèr")).toBe("dereck jeter");
        });

        it('should trim whitespace', () => {
            expect(engine.normalize("  Derek Jeter  ")).toBe("derek jeter");
        });
    });

    describe('Scoring', () => {
        it('should return correct scores for each clue index', () => {
            expect(engine.calculateScore(0)).toBe(10);
            expect(engine.calculateScore(2)).toBe(4);
            expect(engine.calculateScore(4)).toBe(0);
        });
    });

    describe('submitGuess', () => {
        const allPlayers = ["Derek Jeter", "Alex Rodriguez", "Mariano Rivera"];

        it('should return CORRECT for a match', () => {
            const result = engine.submitGuess("Derek Jeter", allPlayers);
            expect(result.status).toBe('CORRECT');
            expect(result.score).toBe(10);
            expect(engine.isComplete).toBe(true);
        });

        it('should return INCORRECT_VALID_PLAYER for a wrong but valid player', () => {
            const result = engine.submitGuess("Alex Rodriguez", allPlayers);
            expect(result.status).toBe('INCORRECT_VALID_PLAYER');
            expect(engine.currentClueIndex).toBe(1);
            expect(engine.isComplete).toBe(false);
        });

        it('should return INVALID_PLAYER for a name not in the list', () => {
            const result = engine.submitGuess("Not A Player", allPlayers);
            expect(result.status).toBe('INVALID_PLAYER');
            expect(engine.currentClueIndex).toBe(0); // No penalty
        });

        it('should return DUPLICATE_GUESS for repeated wrong answers', () => {
            engine.submitGuess("Alex Rodriguez", allPlayers);
            const result = engine.submitGuess("Alex Rodriguez", allPlayers);
            expect(result.status).toBe('DUPLICATE_GUESS');
            expect(engine.currentClueIndex).toBe(1); // No double penalty
        });
    });
});
