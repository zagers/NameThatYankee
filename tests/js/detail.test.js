import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock initScoreDisplay since we don't need it for redirect tests
vi.mock('./scoreDisplay.js', () => ({
    initScoreDisplay: vi.fn()
}));

describe('detail.js redirect logic', () => {
    let originalLocation;

    beforeEach(async () => {
        vi.resetModules();
        localStorage.clear();
        
        // Mock window.location
        originalLocation = window.location;
        delete window.location;
        window.location = {
            pathname: '/2026-04-26.html',
            search: '',
            origin: 'https://namethatyankeequiz.com',
            replace: vi.fn()
        };
    });

    afterEach(() => {
        window.location = originalLocation;
    });

    it('should redirect to quiz if puzzle is not solved and no reveal flag', async () => {
        // Import the module
        await import('../../js/detail.js');
        
        // Dispatch DOMContentLoaded manually
        document.dispatchEvent(new Event('DOMContentLoaded'));
        
        expect(window.location.replace).toHaveBeenCalledWith('quiz?date=2026-04-26');
    });

    it('should NOT redirect if reveal=true flag is present', async () => {
        window.location.search = '?reveal=true';
        
        await import('../../js/detail.js');
        document.dispatchEvent(new Event('DOMContentLoaded'));
        
        expect(window.location.replace).not.toHaveBeenCalled();
    });

    it('should NOT redirect if puzzle is already solved', async () => {
        localStorage.setItem('nameThatYankeeCompletedPuzzles', JSON.stringify(['2026-04-26']));
        
        await import('../../js/detail.js');
        document.dispatchEvent(new Event('DOMContentLoaded'));
        
        expect(window.location.replace).not.toHaveBeenCalled();
    });
});
