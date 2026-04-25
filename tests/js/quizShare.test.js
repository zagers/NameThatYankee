import { describe, it, expect, vi, beforeEach } from 'vitest';
import { generateShareText, copyShareText } from '../../js/quizShare.js';

describe('quizShare', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });
    describe('generateShareText', () => {
        it('should generate correct share text for a win', () => {
            const dateStr = 'April 20, 2026';
            const state = {
                shareEvents: ['hint', 'miss', 'hit'],
                finalScore: 85,
                hintsRequested: 1
            };
            const url = 'https://namethatyankeequiz.com/';
            
            const expected = `Name That Yankee - April 20, 2026\n` +
                `⚾ Score: 85 pts\n` +
                `💡 Hints used: 1\n` +
                `📘🟥🟩\n\n` +
                `https://namethatyankeequiz.com/`;
            
            expect(generateShareText(dateStr, state, url)).toBe(expected);
        });

        it('should generate correct share text for a loss', () => {
            const dateStr = 'April 21, 2026';
            const state = {
                shareEvents: ['hint', 'miss', 'miss', 'miss'],
                finalScore: 0,
                hintsRequested: 1
            };
            const url = 'https://namethatyankeequiz.com/';
            
            const expected = `Name That Yankee - April 21, 2026\n` +
                `⚾ Score: 0 pts\n` +
                `💡 Hints used: 1\n` +
                `📘🟥🟥🟥\n\n` +
                `https://namethatyankeequiz.com/`;
            
            expect(generateShareText(dateStr, state, url)).toBe(expected);
        });

        it('should handle zero hints used', () => {
            const dateStr = 'April 22, 2026';
            const state = {
                shareEvents: ['hit'],
                finalScore: 100,
                hintsRequested: 0
            };
            const url = 'https://namethatyankeequiz.com/';
            
            const expected = `Name That Yankee - April 22, 2026\n` +
                `⚾ Score: 100 pts\n` +
                `💡 Hints used: 0\n` +
                `🟩\n\n` +
                `https://namethatyankeequiz.com/`;
            
            expect(generateShareText(dateStr, state, url)).toBe(expected);
        });
    });

    describe('copyShareText', () => {
        it('should use navigator.share if available', async () => {
            const state = {
                shareEvents: ['hit'],
                finalScore: 100,
                hintsRequested: 0
            };
            const dateStr = 'April 22, 2026';
            
            // Mock navigator.share
            const shareMock = vi.fn().mockResolvedValue(undefined);
            Object.assign(navigator, { share: shareMock });

            await copyShareText(dateStr, state);

            expect(shareMock).toHaveBeenCalled();
            const shareData = shareMock.mock.calls[0][0];
            expect(shareData.text).toContain('Name That Yankee - April 22, 2026');
            expect(shareData.text).toContain('Score: 100 pts');
        });

        it('should fallback to clipboard if navigator.share is not available', async () => {
            const state = {
                shareEvents: ['hit'],
                finalScore: 100,
                hintsRequested: 0
            };
            const dateStr = 'April 22, 2026';
            
            // Mock navigator.share as undefined
            Object.defineProperty(navigator, 'share', {
                value: undefined,
                configurable: true
            });

            // Mock navigator.clipboard
            const writeTextMock = vi.fn().mockResolvedValue(undefined);
            Object.assign(navigator, {
                clipboard: {
                    writeText: writeTextMock
                }
            });

            await copyShareText(dateStr, state);

            expect(writeTextMock).toHaveBeenCalled();
            const copiedText = writeTextMock.mock.calls[0][0];
            expect(copiedText).toContain('Name That Yankee - April 22, 2026');
        });
    });
});
