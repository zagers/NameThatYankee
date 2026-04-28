// ABOUTME: Controls the interactive player detail view after puzzle completion.
// ABOUTME: Manages follow-up questions and career summary visualizations.

import { initScoreDisplay } from './scoreDisplay.js';

/**
 * Checks if the user should be allowed to view the answer page.
 * Redirects to the quiz if the puzzle isn't solved and no bypass flag is present.
 */
function handleRedirect() {
    // Stricter regex to ensure we only match dates at the end of the path (e.g., /2026-04-26 or /2026-04-26.html)
    // Added optional trailing slash support for robustness
    const path = window.location.pathname;
    const dateMatch = path.match(/\/(\d{4}-\d{2}-\d{2})(?:\.html)?\/?$/);
    
    if (dateMatch) {
        const date = dateMatch[1];
        const params = new URLSearchParams(window.location.search);
        const reveal = params.get('reveal') === 'true';
        
        // Detect common search engine bots (Google, Bing, Yahoo, DuckDuckGo, etc.)
        // to allow indexing of answer pages without forcing a redirect.
        const isBot = /bot|crawler|spider|crawling|slurp|bingbot|googlebot/i.test(navigator.userAgent);
        if (isBot) return;

        let completedPuzzles = [];
        try {
            completedPuzzles = JSON.parse(localStorage.getItem('nameThatYankeeCompletedPuzzles') || '[]');
        } catch (e) {
            console.error('Failed to parse completed puzzles from localStorage', e);
        }
        
        const isSolved = Array.isArray(completedPuzzles) && completedPuzzles.includes(date);

        if (!isSolved && !reveal) {
            // Derive the base path (everything before the date part of the URL)
            // to support both root and subdirectory hosting (e.g. GitHub Pages)
            const basePath = path.substring(0, dateMatch.index + 1);
            const redirectUrl = new URL(basePath + 'quiz', window.location.origin);
            redirectUrl.searchParams.set('date', date);
            window.location.replace(redirectUrl.toString());
        }
    }
}

// Execute redirect check immediately to prevent flashing the answer page
handleRedirect();

document.addEventListener('DOMContentLoaded', () => {
    initScoreDisplay();
});
