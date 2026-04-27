// ABOUTME: Controls the interactive player detail view after puzzle completion.
// ABOUTME: Manages follow-up questions and career summary visualizations.

import { initScoreDisplay } from './scoreDisplay.js';

/**
 * Checks if the user should be allowed to view the answer page.
 * Redirects to the quiz if the puzzle isn't solved and no bypass flag is present.
 */
function handleRedirect() {
    const path = window.location.pathname;
    const dateMatch = path.match(/(\d{4}-\d{2}-\d{2})/);
    
    if (dateMatch) {
        const date = dateMatch[1];
        const params = new URLSearchParams(window.location.search);
        const reveal = params.get('reveal') === 'true';
        
        let completedPuzzles = [];
        try {
            completedPuzzles = JSON.parse(localStorage.getItem('nameThatYankeeCompletedPuzzles') || '[]');
        } catch (e) {
            console.error('Failed to parse completed puzzles from localStorage', e);
        }
        
        const isSolved = Array.isArray(completedPuzzles) && completedPuzzles.includes(date);

        if (!isSolved && !reveal) {
            // Use replace to avoid keeping the answer page in the history stack
            window.location.replace(`quiz?date=${date}`);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    handleRedirect();
    initScoreDisplay();
});
