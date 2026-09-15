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
    it('returns empty for empty query', () => {
        expect(searchPuzzles(PUZZLES, '')).toEqual([]);
    });

    it('finds exact name match', () => {
        const results = searchPuzzles(PUZZLES, 'Billy Martin');
        expect(results[0].puzzle.name).toBe('Billy Martin');
        expect(results[0].score).toBe(20);
    });

    it('finds by substring of last name', () => {
        const results = searchPuzzles(PUZZLES, 'martin');
        expect(results.map(r => r.puzzle.name)).toEqual(['Billy Martin']);
    });

    it('finds by nickname alias', () => {
        const results = searchPuzzles(PUZZLES, 'billy');
        expect(results.some(r => r.puzzle.name === 'Billy Martin')).toBe(true);
        expect(results.some(r => r.puzzle.name === 'Aaron Judge')).toBe(false);
    });

    it('finds by fuzzy typo', () => {
        const results = searchPuzzles(PUZZLES, 'mrtin');
        expect(results.some(r => r.puzzle.name === 'Billy Martin')).toBe(true);
    });

    it('reports nothing for unknown multi-token nickname', () => {
        const results = searchPuzzles(PUZZLES, 'home run baker');
        expect(results).toEqual([]);
    });

    it('returns empty array for nonsense', () => {
        expect(searchPuzzles(PUZZLES, 'zzzzzzzzz')).toEqual([]);
    });

    it('respects required fields parameter (name only)', () => {
        const node = { date: '2026-09-11', name: 'Aaron Judge', nicknames: ['Sevy'], career_totals: {}, teams: [], years: [] };
        const results = searchPuzzles([...PUZZLES, node], 'sevy', ['name']);
        expect(results).toEqual([]);
    });
});
