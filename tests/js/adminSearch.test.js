import { describe, it, expect } from 'vitest';
import { normalizeAdminText, levenshtein, searchPuzzles } from '../../js/adminSearch.js';

const PUZZLES = [
    { date: '2026-09-14', name: 'Billy Martin', nicknames: ['Billy'], career_totals: { WAR: '62.0' }, teams: ['NYY'], years: ['1950'] },
    { date: '2026-09-11', name: 'Aaron Judge', nicknames: ['AJ'], career_totals: { WAR: '62.9' }, teams: ['NYY'], years: ['2016'] },
];

describe('normalizeAdminText', () => {
    it('lowercases and trims', () => {
        expect(normalizeAdminText('  Billy Martin ')).toBe('billy martin');
    });

    it('strips diacritics', () => {
        expect(normalizeAdminText('José Abreu')).toBe('jose abreu');
    });

    it('handles null/undefined', () => {
        expect(normalizeAdminText(null)).toBe('');
        expect(normalizeAdminText(undefined)).toBe('');
    });
});

describe('levenshtein', () => {
    it('returns 0 for identical strings', () => {
        expect(levenshtein('abc', 'abc')).toBe(0);
    });

    it('calculates insertions', () => {
        expect(levenshtein('abc', 'abcd')).toBe(1);
    });

    it('calculates deletions', () => {
        expect(levenshtein('abc', 'ab')).toBe(1);
    });

    it('calculates substitutions', () => {
        expect(levenshtein('abc', 'axc')).toBe(1);
    });
});

describe('searchPuzzles', () => {
    it('finds exact name match with score 0', () => {
        const results = searchPuzzles(PUZZLES, 'Billy Martin');
        expect(results.length).toBeGreaterThanOrEqual(1);
        expect(results[0].puzzle.name).toBe('Billy Martin');
        expect(results[0].score).toBe(0);
    });

    it('finds by nickname', () => {
        const results = searchPuzzles(PUZZLES, 'AJ');
        expect(results.some(r => r.puzzle.name === 'Aaron Judge')).toBe(true);
    });

    it('finds fuzzy matches within threshold', () => {
        const results = searchPuzzles(PUZZLES, 'Bily Martn');
        expect(results.some(r => r.puzzle.name === 'Billy Martin')).toBe(true);
    });

    it('returns empty array for nonsense', () => {
        const results = searchPuzzles(PUZZLES, 'zzzzzzzzz');
        expect(results).toEqual([]);
    });
});
