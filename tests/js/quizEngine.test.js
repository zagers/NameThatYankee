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
});
