import { describe, it, expect } from 'vitest';
import { normalizeText, validateGuess, calculateScore, getAutocompleteSuggestions } from '../../js/quizEngine.js';

describe('quizEngine', () => {
    describe('normalizeText', () => {
        it('should handle diacritics and capitalization', () => {
            expect(normalizeText('Rémý')).toBe('remy');
            expect(normalizeText('A-Rod')).toBe('a-rod');
        });

        it('should handle empty input', () => {
            expect(normalizeText('')).toBe('');
            expect(normalizeText(null)).toBe('');
            expect(normalizeText(undefined)).toBe('');
        });
    });

    describe('validateGuess', () => {
        const allPlayers = ['Aaron Judge', 'Derek Jeter', 'Mariano Rivera'];
        const normalizedPlayers = allPlayers.map(p => normalizeText(p));
        const correctAnswer = 'derek jeter';
        const nickname = 'the captain';

        it('should return CORRECT when guess matches answer', () => {
            expect(validateGuess('Derek Jeter', correctAnswer, normalizedPlayers)).toEqual({ status: 'CORRECT' });
            expect(validateGuess('derek jeter', correctAnswer, normalizedPlayers)).toEqual({ status: 'CORRECT' });
        });

        it('should return CORRECT when guess matches nickname', () => {
            expect(validateGuess('The Captain', correctAnswer, normalizedPlayers, nickname)).toEqual({ status: 'CORRECT' });
            expect(validateGuess('the captain', correctAnswer, normalizedPlayers, nickname)).toEqual({ status: 'CORRECT' });
        });

        it('should handle diacritics and special characters in answer, guess, and nickname', () => {
            const diacriticsAnswer = 'José Altuve';
            const diacriticsNickname = 'Tuve';
            expect(validateGuess('Jose Altuve', diacriticsAnswer, normalizedPlayers)).toEqual({ status: 'CORRECT' });
            expect(validateGuess('josé altuve', diacriticsAnswer, normalizedPlayers)).toEqual({ status: 'CORRECT' });
            expect(validateGuess('tuve', diacriticsAnswer, normalizedPlayers, diacriticsNickname)).toEqual({ status: 'CORRECT' });
        });

        it('should return INCORRECT_VALID_PLAYER when guess is wrong but valid', () => {
            expect(validateGuess('aaron judge', correctAnswer, normalizedPlayers)).toEqual({ status: 'INCORRECT_VALID_PLAYER' });
        });

        it('should return INVALID_PLAYER when guess is not in player list', () => {
            expect(validateGuess('LeBron James', correctAnswer, normalizedPlayers)).toEqual({ status: 'INVALID_PLAYER' });
        });
    });

    describe('calculateScore', () => {
        const pointsArray = [10, 7, 4, 1, 0];

        it('should return correct points based on hints revealed', () => {
            expect(calculateScore(0, pointsArray)).toBe(10);
            expect(calculateScore(2, pointsArray)).toBe(4);
            expect(calculateScore(4, pointsArray)).toBe(0);
        });

        it('should return 0 when hints revealed exceed points array', () => {
            expect(calculateScore(5, pointsArray)).toBe(0);
        });
    });

    describe('getAutocompleteSuggestions', () => {
        const allPlayers = ['Aaron Judge', 'Aaron Boone', 'Aaron Hicks', 'Babe Ruth'];

        it('should return matching players for 2 or more characters', () => {
            expect(getAutocompleteSuggestions('aa', allPlayers)).toEqual(['Aaron Judge', 'Aaron Boone', 'Aaron Hicks']);
            expect(getAutocompleteSuggestions('bab', allPlayers)).toEqual(['Babe Ruth']);
        });

        it('should be case insensitive', () => {
            expect(getAutocompleteSuggestions('AAR', allPlayers)).toEqual(['Aaron Judge', 'Aaron Boone', 'Aaron Hicks']);
        });

        it('should return empty array for less than 2 characters', () => {
            expect(getAutocompleteSuggestions('a', allPlayers)).toEqual([]);
        });

        it('should respect maxSuggestions default (7)', () => {
            const longList = Array(10).fill('Test Player');
            expect(getAutocompleteSuggestions('te', longList).length).toBe(7);
        });

        it('should respect custom maxSuggestions', () => {
            const longList = Array(10).fill('Test Player');
            expect(getAutocompleteSuggestions('te', longList, 3).length).toBe(3);
        });
    });
});
