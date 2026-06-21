import { describe, it, expect, beforeEach } from 'vitest';
import { QuizEngine, normalizeText } from '../../js/quizEngine.js';

describe('QuizEngine', () => {
    let engine;
    const answer = "Derek Jeter";
    const clues = ["Clue 1", "Clue 2", "Clue 3"];
    const allPlayers = ["Derek Jeter", "Alex Rodriguez", "Mariano Rivera"];
    const normalizedPlayerSet = new Set(allPlayers.map(p => normalizeText(p)));

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
        it('should return CORRECT for a match', () => {
            const result = engine.submitGuess("Derek Jeter", normalizedPlayerSet);
            expect(result.status).toBe('CORRECT');
            expect(result.score).toBe(10);
            expect(engine.isComplete).toBe(true);
        });

        it('should accept any nickname from an array as correct', () => {
            const engineWithNicknames = new QuizEngine(answer, clues, ["Captain", "Mr. November"]);
            const result = engineWithNicknames.submitGuess("Mr. November", normalizedPlayerSet);
            expect(result.status).toBe('CORRECT');
            expect(result.score).toBe(10);
        });

        it('should accept the first nickname from an array as correct', () => {
            const engineWithNicknames = new QuizEngine(answer, clues, ["Captain", "Mr. November"]);
            const result = engineWithNicknames.submitGuess("Captain", normalizedPlayerSet);
            expect(result.status).toBe('CORRECT');
        });

        it('should accept a single nickname string for backward compatibility', () => {
            const engineWithNickname = new QuizEngine(answer, clues, "Captain");
            const result = engineWithNickname.submitGuess("Captain", normalizedPlayerSet);
            expect(result.status).toBe('CORRECT');
        });

        it('should work with empty nicknames array', () => {
            const engineNoNicknames = new QuizEngine(answer, clues, []);
            const result = engineNoNicknames.submitGuess("Not Derek", normalizedPlayerSet);
            expect(result.status).not.toBe('CORRECT');
        });

        it('should work with no nicknames argument', () => {
            const result = engine.submitGuess("Captain", normalizedPlayerSet);
            expect(result.status).not.toBe('CORRECT');
        });

        it('should return INCORRECT_VALID_PLAYER for a wrong but valid player', () => {
            const result = engine.submitGuess("Alex Rodriguez", normalizedPlayerSet);
            expect(result.status).toBe('INCORRECT_VALID_PLAYER');
            expect(engine.currentClueIndex).toBe(1);
            expect(engine.isComplete).toBe(false);
        });

        it('should return INVALID_PLAYER for a name not in the list', () => {
            const result = engine.submitGuess("Not A Player", normalizedPlayerSet);
            expect(result.status).toBe('INVALID_PLAYER');
            expect(engine.currentClueIndex).toBe(0); // No penalty
        });

        it('should return DUPLICATE_GUESS for repeated wrong answers', () => {
            engine.submitGuess("Alex Rodriguez", normalizedPlayerSet);
            const result = engine.submitGuess("Alex Rodriguez", normalizedPlayerSet);
            expect(result.status).toBe('DUPLICATE_GUESS');
            expect(engine.currentClueIndex).toBe(1); // No double penalty
        });
    });
});
