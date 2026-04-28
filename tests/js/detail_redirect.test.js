import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock scoreDisplay.js for redirect tests to avoid side effects
vi.mock('../../js/scoreDisplay.js', () => ({
    initScoreDisplay: vi.fn()
}));

describe('detail.js redirect logic', () => {
    let originalLocation;

    beforeEach(async () => {
        vi.resetModules();
        localStorage.clear();
        
        // Mock window.location using Object.defineProperty for stability
        originalLocation = window.location;
        Object.defineProperty(window, 'location', {
            configurable: true,
            value: {
                pathname: '/2026-04-26.html',
                href: 'https://namethatyankeequiz.com/2026-04-26.html',
                search: '',
                origin: 'https://namethatyankeequiz.com',
                replace: vi.fn()
            }
        });
    });

    afterEach(() => {
        Object.defineProperty(window, 'location', {
            configurable: true,
            value: originalLocation
        });
    });

    it('should redirect to quiz if puzzle is not solved and no reveal flag', async () => {
        // Import triggers immediate handleRedirect()
        await import('../../js/detail.js');
        expect(window.location.replace).toHaveBeenCalledWith('https://namethatyankeequiz.com/quiz?date=2026-04-26');
    });

    it('should handle optional trailing slash in redirect logic', async () => {
        window.location.pathname = '/2026-04-26/';
        window.location.href = 'https://namethatyankeequiz.com/2026-04-26/';
        
        await import('../../js/detail.js');
        expect(window.location.replace).toHaveBeenCalledWith('https://namethatyankeequiz.com/quiz?date=2026-04-26');
    });

    it('should support subdirectory hosting in redirect logic', async () => {
        window.location.pathname = '/yankee/2026-04-26';
        window.location.href = 'https://namethatyankeequiz.com/yankee/2026-04-26';
        
        await import('../../js/detail.js');
        expect(window.location.replace).toHaveBeenCalledWith('https://namethatyankeequiz.com/yankee/quiz?date=2026-04-26');
    });

    it('should NOT redirect if reveal=true flag is present', async () => {
        window.location.search = '?reveal=true';
        await import('../../js/detail.js');
        expect(window.location.replace).not.toHaveBeenCalled();
    });

    it('should NOT redirect if puzzle is already solved', async () => {
        localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(['2026-04-26']));
        await import('../../js/detail.js');
        expect(window.location.replace).not.toHaveBeenCalled();
    });

    it('should NOT redirect if user agent is a search bot (e.g. Googlebot)', async () => {
        const originalUserAgent = navigator.userAgent;
        Object.defineProperty(navigator, 'userAgent', {
            value: 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            configurable: true
        });
        
        await import('../../js/detail.js');
        expect(window.location.replace).not.toHaveBeenCalled();
        
        // Reset user agent
        Object.defineProperty(navigator, 'userAgent', {
            value: originalUserAgent,
            configurable: true
        });
    });
});
