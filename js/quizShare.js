// ABOUTME: Social sharing logic for the quiz.
// ABOUTME: Manages Wordle-style emoji grid generation and native sharing APIs.

/**
 * Generates the Wordle-style share text.
 * @param {string} dateStr - Formatted date string (e.g. "April 20, 2026")
 * @param {Object} state - The QuizState object
 * @param {string} url - The site URL to include in the share
 * @returns {string}
 */
export function generateShareText(dateStr, state, url) {
    const isWin = state.shareEvents.includes('hit');
    const pointsEarned = isWin ? state.finalScore : 0;
    
    // Map events to emojis: hint=📘, miss=🟥, hit=🟩
    const emojiMap = {
        'hint': '📘',
        'miss': '🟥',
        'hit': '🟩'
    };
    const emojiGrid = state.shareEvents.map(event => emojiMap[event]).join('');

    return `Name That Yankee - ${dateStr}\n` +
        `⚾ Score: ${pointsEarned} pts\n` +
        `💡 Hints used: ${state.hintsRequested}\n` +
        `${emojiGrid}\n\n` +
        `${url}`;
}

/**
 * Handles the share action using navigator.share or navigator.clipboard.
 * @param {string} dateStr - Formatted date string
 * @param {Object} state - The QuizState object
 * @returns {Promise<void>}
 */
export async function copyShareText(dateStr, state) {
    const url = window.location.href;
    const text = generateShareText(dateStr, state, url);
    
    if (navigator.share) {
        try {
            // Omitting title/url ensures text block is shared correctly on iOS
            await navigator.share({
                text: text
            });
            return;
        } catch (err) {
            if (err.name === 'AbortError') return;
            console.error('Native share failed, falling back to clipboard:', err);
        }
    }

    // Fallback to clipboard
    try {
        await navigator.clipboard.writeText(text);
    } catch (err) {
        console.error('Failed to copy to clipboard:', err);
        throw err; // Task 3 will handle UI feedback and error alerts
    }
}
