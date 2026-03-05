import { describe, it, expect } from 'vitest';
import { processTeamData, processDecadeData, processGuessesData, processToughestPuzzlesData } from '../../js/analyticsData.js';

describe('analyticsData', () => {
    describe('processTeamData', () => {
        const playerData = [
            { teams: ['NYY', 'BOS', 'BAL'] },
            { teams: ['BOS', 'NYY'] },
            { teams: ['CHWTM'] } // Ends with TM, should be excluded
        ];

        it('should correctly count non-NYY and non-TM teams', () => {
            const result = processTeamData(playerData);
            expect(result.labels).toEqual(['BOS', 'BAL']);
            expect(result.data).toEqual([2, 1]); // BOS: 2, BAL: 1
        });

        it('should sort by count descending', () => {
            const moreData = [
                ...playerData,
                { teams: ['BAL'] },
                { teams: ['BAL'] }
            ];
            const result = processTeamData(moreData);
            expect(result.labels).toEqual(['BAL', 'BOS']);
            expect(result.data).toEqual([3, 2]); // BAL: 3, BOS: 2
        });
    });

    describe('processDecadeData', () => {
        const playerData = [
            { years: [1995, '1998', 2001] }, // Player 1 played 1990s and 2000s
            { years: ['2005', 2010] }, // Player 2 played 2000s and 2010s
        ];

        it('should correctly tally decade counts and sort them', () => {
            const result = processDecadeData(playerData);
            expect(result.labels).toEqual(['1990s', '2000s', '2010s']);
            expect(result.data).toEqual([1, 2, 1]); // 1990s: 1, 2000s: 2, 2010s: 1
            expect(result.originalDecades).toEqual(['1990', '2000', '2010']);
        });
    });

    describe('processGuessesData', () => {
        const guessData = [
            { guessText: 'Aaron Judge' },
            { guessText: 'Derek Jeter' },
            { guessText: 'aaron judge' }, // should be case insensitive tally
        ];

        it('should group guesses by name, sort, and capitalize', () => {
            const result = processGuessesData(guessData);
            expect(result.labels).toEqual(['Aaron Judge', 'Derek Jeter']);
            expect(result.data).toEqual([2, 1]);
        });
    });

    describe('processToughestPuzzlesData', () => {
        const guessData = [
            { puzzleDate: '2025-05-15' },
            { puzzleDate: '2025-06-01' },
            { puzzleDate: '2025-05-15' },
        ];

        it('should group incorrectly answered puzzles, format dates, and sort', () => {
            const result = processToughestPuzzlesData(guessData);
            expect(result.data).toEqual([2, 1]);
            expect(result.originalDates).toEqual(['2025-05-15', '2025-06-01']);
        });
    });
});
