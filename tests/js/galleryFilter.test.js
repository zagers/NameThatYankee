import { describe, it, expect } from 'vitest';
import { checkMatch } from '../../js/galleryFilter.js';

describe('galleryFilter', () => {
    describe('checkMatch', () => {
        const samplePuzzle = {
            date: "2026-04-19",
            name: "Lou Piniella",
            nickname: "Sweet Lou",
            teams: ["NYY", "BAL", "KCR", "CLE"],
            years: ["1970", "1980", "1978"]
        };

        it('should show all when no search tokens', () => {
            expect(checkMatch(samplePuzzle, false, [])).toBe(true);
        });

        it('should filter by team abbreviation', () => {
            expect(checkMatch(samplePuzzle, false, ['nyy'])).toBe(true);
            expect(checkMatch(samplePuzzle, false, ['oak'])).toBe(false);
        });

        it('should filter by team full name', () => {
            expect(checkMatch(samplePuzzle, false, ['yankees'])).toBe(true);
            expect(checkMatch(samplePuzzle, false, ['baltimore'])).toBe(true);
            expect(checkMatch(samplePuzzle, false, ['dodgers'])).toBe(false);
        });

        it('should filter by year', () => {
            expect(checkMatch(samplePuzzle, false, ['1970'])).toBe(true);
            expect(checkMatch(samplePuzzle, false, ['2024'])).toBe(false);
        });

        it('should filter by decade (90s)', () => {
            const ninetyPuzzle = { ...samplePuzzle, years: ["1995", "1998"] };
            expect(checkMatch(ninetyPuzzle, false, ['90s'])).toBe(true);
            expect(checkMatch(samplePuzzle, false, ['90s'])).toBe(false);
        });

        it('should filter by long decade (1990s)', () => {
            const ninetyPuzzle = { ...samplePuzzle, years: ["1995", "1998"] };
            expect(checkMatch(ninetyPuzzle, false, ['1990s'])).toBe(true);
        });

        it('should filter by month name', () => {
            expect(checkMatch(samplePuzzle, false, ['april'])).toBe(true);
            expect(checkMatch(samplePuzzle, false, ['june'])).toBe(false);
        });

        it('should require all tokens in search query (AND logic)', () => {
            expect(checkMatch(samplePuzzle, false, ['nyy', '1980'])).toBe(true);
            expect(checkMatch(samplePuzzle, false, ['nyy', '1999'])).toBe(false);
        });

        it('should protect spoilers (no name match if unsolved)', () => {
            expect(checkMatch(samplePuzzle, false, ['lou'])).toBe(false);
            expect(checkMatch(samplePuzzle, false, ['piniella'])).toBe(false);
            expect(checkMatch(samplePuzzle, false, ['sweet'])).toBe(false);
        });

        it('should allow name/nickname match if solved', () => {
            expect(checkMatch(samplePuzzle, true, ['lou'])).toBe(true);
            expect(checkMatch(samplePuzzle, true, ['piniella'])).toBe(true);
            expect(checkMatch(samplePuzzle, true, ['sweet lou'])).toBe(true);
        });
    });
});
